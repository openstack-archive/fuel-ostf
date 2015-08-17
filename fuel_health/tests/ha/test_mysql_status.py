# Copyright 2015 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging

from fuel_health.common.ssh import Client as SSHClient
from fuel_health.test import BaseTestCase

LOG = logging.getLogger(__name__)


class BaseMysqlTest(BaseTestCase):
    """Base methods for MySQL DB tests
    """
    @classmethod
    def setUpClass(cls):
        super(BaseMysqlTest, cls).setUpClass()
        cls.nodes = cls.config.compute.nodes
        cls.controller_ip = cls.config.compute.online_controllers[0]
        cls.node_key = cls.config.compute.path_to_private_key
        cls.node_user = cls.config.compute.ssh_user
        cls.mysql_user = 'root'
        cls.master_ip = []
        cls.one_db_msg = "There is only one database online. " \
                         "Nothing to check'"
        cls.no_db_msg = "Can not find any online database. Check that at " \
                        "least one database is operable"

    def setUp(self):
        super(BaseMysqlTest, self).setUp()
        if 'ha' not in self.config.compute.deployment_mode:
            self.skipTest('Cluster is not HA mode, skipping tests')

    @classmethod
    def get_database_nodes(cls, controller_ip, username, key):
        # retrieve data from controller
        ssh_client = SSHClient(controller_ip,
                               username,
                               key_filename=key,
                               timeout=100)

        hiera_cmd = 'ruby -e \'require "hiera";' \
                    'db = Hiera.new().lookup("database_nodes", {}, {}).keys;'\
                    'if db != [] then puts db else puts "None" end\''
        database_nodes = ssh_client.exec_command(hiera_cmd)
        # backward compatibility for upgraded fuel
        if 'None' in database_nodes:
            return cls.config.compute.online_controllers

        # get online nodes
        database_nodes = database_nodes.splitlines()
        databases = []
        for node in cls.config.compute.nodes:
            hostname = node['hostname']
            if hostname in database_nodes and node['online']:
                databases.append(hostname)
        return databases


class TestMysqlStatus(BaseMysqlTest):
    @classmethod
    def setUpClass(cls):
        super(TestMysqlStatus, cls).setUpClass()

    def setUp(self):
        super(TestMysqlStatus, self).setUp()
        if 'ha' not in self.config.compute.deployment_mode:
            self.skipTest('Cluster is not HA mode, skipping tests')

    def test_os_databases(self):
        """Check if amount of tables in databases is the same on each node
        Target Service: HA mysql

        Scenario:
            1. Detect there are online database nodes.
            2. Request list of tables for os databases on each node.
            3. Check if amount of tables in databases is the same on each node
        Duration: 10 s.
        """
        LOG.info("'Test OS Databases' started")
        dbs = ['nova', 'glance', 'keystone']
        cmd = "mysql -h localhost -e 'SHOW TABLES FROM %(database)s'"

        databases = self.verify(20, self.get_database_nodes,
                                1, "Can not get database hostnames. Check that"
                                   " at least one controller is operable",
                                "get database nodes",
                                self.controller_ip,
                                self.node_user,
                                key=self.node_key)

        self.verify_response_body_not_equal(0, len(databases),
                                            self.no_db_msg, 1)
        if len(databases) == 1:
            self.skipTest(self.one_db_msg)

        for database in dbs:
            LOG.info('Current database name is %s' % database)
            temp_set = set()
            for node in databases:
                LOG.info('Current database node is %s' % node)
                cmd1 = cmd % {'database': database}
                LOG.info('Try to execute command %s' % cmd1)
                tables = SSHClient(
                    node, self.node_user,
                    key_filename=self.node_key,
                    timeout=self.config.compute.ssh_timeout)
                output = self.verify(40, tables.exec_command, 2,
                                     'Can list tables',
                                     'get amount of tables for each database',
                                     cmd1)
                tables = set(output.splitlines())
                if len(temp_set) == 0:
                    temp_set = tables
                self.verify_response_true(
                    len(tables.symmetric_difference(temp_set)) == 0,
                    "Step 3 failed: Tables in %s database are "
                    "different" % database)

            del temp_set

    @staticmethod
    def get_variables_from_output(output, variables):
        """Return dict with variables and their values extracted from mysql
        Assume that output is "| Var_name | Value |"
        """
        result = {}
        LOG.debug('Expected variables: "{0}"'.format(str(variables)))
        for line in output:
            try:
                var, value = line.strip("| ").split("|")[:2]
            except ValueError:
                continue
            var = var.strip()
            if var in variables:
                result[var] = value.strip()
        LOG.debug('Extracted values: "{0}"'.format(str(result)))
        return result

    def test_state_of_galera_cluster(self):
        """Check galera environment state
        Target Service: HA mysql

        Scenario:
            1. Detect there are online database nodes.
            2. Ssh on each node containing database and request state of galera
               node
            3. For each node check cluster size
            4. For each node check status is ready
            5. For each node check that node is connected to cluster
        Duration: 10 s.
        """
        databases = self.verify(20, self.get_database_nodes,
                                1, "Can not get database hostnames. Check that"
                                   " at least one controller is operable",
                                "get database nodes",
                                self.controller_ip,
                                self.node_user,
                                key=self.node_key)

        self.verify_response_body_not_equal(0, len(databases),
                                            self.no_db_msg, 1)
        if len(databases) == 1:
            self.skipTest(self.one_db_msg)

        for db_node in databases:
            command = "mysql -h localhost -e \"SHOW STATUS LIKE 'wsrep_%'\""
            ssh_client = SSHClient(db_node, self.node_user,
                                   key_filename=self.node_key,
                                   timeout=100)
            output = self.verify(
                20, ssh_client.exec_command, 2,
                "Verification of galera cluster node status failed",
                'get status from galera node',
                command).splitlines()

            LOG.debug('mysql output from node "{0}" is \n"{1}"'.format(
                db_node, output)
            )

            mysql_vars = [
                'wsrep_cluster_size',
                'wsrep_ready',
                'wsrep_connected'
            ]
            result = self.get_variables_from_output(output, mysql_vars)

            self.verify_response_body_content(
                result.get('wsrep_cluster_size', 0),
                str(len(databases)),
                msg='Cluster size on %s less '
                    'than databases count' % db_node,
                failed_step='3')

            self.verify_response_body_content(
                result.get('wsrep_ready', 'OFF'), 'ON',
                msg='wsrep_ready on %s is not ON' % db_node,
                failed_step='4')

            self.verify_response_body_content(
                result.get('wsrep_connected', 'OFF'), 'ON',
                msg='wsrep_connected on %s is not ON' % db_node,
                failed_step='5')
