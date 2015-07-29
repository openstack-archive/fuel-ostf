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
import fuel_health.test

LOG = logging.getLogger(__name__)


class TestMysqlStatus(fuel_health.test.BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestMysqlStatus, cls).setUpClass()
        cls.controller_ip = cls.config.compute.online_controllers[0]
        cls.controllers = cls.config.compute.online_controllers
        cls.controller_key = cls.config.compute.path_to_private_key
        cls.controller_user = cls.config.compute.ssh_user
        cls.mysql_user = 'root'
        cls.master_ip = []

    def setUp(self):
        super(TestMysqlStatus, self).setUp()
        if 'ha' not in self.config.compute.deployment_mode:
            self.skipTest('Cluster is not HA mode, skipping tests')
        if len(self.controllers) == 1:
            self.skipTest('There is only one controller online. '
                          'Nothing to check')

    def test_os_databases(self):
        """Check amount of tables in databases is the same on each node
        Target Service: HA mysql

        Scenario:
            1. Request list of tables for os databases on each node.
            2. Check that amount of tables for each database is the same
        Duration: 100 s.
        """
        dbs = ['nova', 'glance', 'keystone']
        cmd = "mysql -e 'SHOW TABLES FROM %(database)s'"
        for database in dbs:
            LOG.info('Current database name is %s' % database)
            temp_set = set()
            for node in self.config.compute.online_controllers:
                LOG.info('Current controller node is %s' % node)
                cmd1 = cmd % {'database': database}
                LOG.info('Try to execute command %s' % cmd1)
                tables = SSHClient(
                    node, self.controller_user,
                    key_filename=self.controller_key,
                    timeout=self.config.compute.ssh_timeout)
                output = self.verify(40, tables.exec_command, 1,
                                     'Can list tables',
                                     'get amount of tables for each database',
                                     cmd1)
                tables = set(output.splitlines())
                if len(temp_set) == 0:
                    temp_set = tables
                self.verify_response_true(
                    len(tables.symmetric_difference(temp_set)) == 0,
                    "Step 2 failed: Tables in %s database are "
                    "different" % database)

            del temp_set

    def test_state_of_mysql_cluster(self):
        """Check mysql environment state
        Target Service: HA mysql

        Scenario:
            1. Detect mysql master node.
            2. Ssh on mysql-master node and request its status
            3. Verify that position field is not empty
            4. Ssh on mysql-slave nodes and request their statuses
            5. Verify that  Slave_IO_State is in appropriate state
            6. Verify that Slave_IO_Running is in appropriate state
            7. Verify that Slave_SQL_Running is in appropriate state
        Duration: 100 s.
        Deployment tags: RHEL
        """

        if 'RHEL' in self.config.compute.deployment_os:
            # Find mysql master node
            master_node_ip = []
            cmd = 'mysql -e "SHOW SLAVE STATUS\G"'
            LOG.info("Controllers nodes are %s" % self.controllers)
            for controller_ip in self.controllers:
                ssh_client = SSHClient(controller_ip, self.controller_user,
                                       key_filename=self.controller_key,
                                       timeout=100)
                output = self.verify(20, ssh_client.exec_command, 1,
                                     'Can not define master node',
                                     'master mode detection', cmd)
                LOG.info('output is %s' % output)
                if not output:
                    self.master_ip.append(controller_ip)
                    master_node_ip.append(controller_ip)

            # ssh on master node and check status
            check_master_state_cmd = 'mysql -e "SHOW MASTER STATUS\G"'
            ssh_client = SSHClient(self.master_ip[0], self.controller_user,
                                   key_filename=self.controller_key,
                                   timeout=100)
            output = self.verify(20, ssh_client.exec_command, 2,
                                 'Can not execute "SHOW MASTER STATUS" '
                                 'command', 'check master status',
                                 check_master_state_cmd).splitlines()[1:]
            LOG.info('master output is %s' % output)
            res = [data.strip().split(':') for data in output]
            master_dict = dict((k, v) for (k, v) in res)
            self.verify_response_body_not_equal(
                master_dict['Position'], '',
                msg='Position field is empty. Master is offline',
                failed_step='3')

            # ssh on slave node and check it status
            check_slave_state_cmd = 'mysql -e "SHOW SLAVE STATUS\G"'

            for controller in self.controllers:
                if controller not in self.master_ip:
                    client = SSHClient(controller,
                                       self.controller_user,
                                       key_filename=self.controller_key)
                    output = self.verify(
                        20, client.exec_command, 4,
                        'Failed to get slave status', 'get slave status',
                        check_slave_state_cmd).splitlines()[1:19]

                    LOG.info("slave output is %s" % output)
                    res = [data.strip().split(':') for data in output]
                    slave_dict = dict((k, v) for (k, v) in res)
                    self.verify_response_body(
                        slave_dict['Slave_IO_State'],
                        ' Waiting for master to send event',
                        msg='Slave IO state is incorrect ',
                        failed_step='5')

                    self.verify_response_body(
                        slave_dict['Slave_IO_Running'],
                        ' Yes', msg='Slave_IO_Running state is incorrect',
                        failed_step='6')

                    self.verify_response_body(
                        slave_dict['Slave_SQL_Running'],
                        ' Yes', msg='Slave_SQL_Running state is incorrect',
                        failed_step='7')
        else:
            self.skipTest("There is no RHEL deployment")

    @staticmethod
    def get_variables_from_output(output, variables):
        """ Get values for variables, listed in 'variables' argument and
        return dict
        Assume that output is "| Var_name | Value |"
        """
        result = {}
        for line in output:
            if line.startswith("+"):
                continue
            temp = line[1:]  # slice first |
            var, value = temp.split("|")[:2]
            var = var.strip()
            if var in variables:
                result[var] = value.strip()
        return result

    def test_state_of_galera_cluster(self):
        """Check galera environment state
        Target Service: HA mysql

        Scenario:
            1. Ssh on each controller and request state of galera node
            2. For each node check cluster size
            3. For each node check status is ready
            4. For each node check that node is connected to cluster
        Duration: 60 s.
        Deployment tags: CENTOS
        """
        if 'CentOS' in self.config.compute.deployment_os:
            for controller in self.controllers:
                command = "mysql -e \"SHOW STATUS LIKE 'wsrep_%'\""
                ssh_client = SSHClient(controller, self.controller_user,
                                       key_filename=self.controller_key,
                                       timeout=100)
                output = self.verify(
                    20, ssh_client.exec_command, 1,
                    "Verification of galera cluster node status failed",
                    'get status from galera node',
                    command).splitlines()

                LOG.debug('output is %s' % output)

                mysql_vars = [
                    'wsrep_cluster_size',
                    'wsrep_ready',
                    'wsrep_connected'
                ]
                result = self.get_variables_from_output(output, mysql_vars)

                self.verify_response_body_content(
                    result.get('wsrep_cluster_size', 0),
                    str(len(self.controllers)),
                    msg='Cluster size on %s less '
                        'than controllers count' % controller,
                    failed_step='2')

                self.verify_response_body_content(
                    result.get(('wsrep_ready', 'OFF')), 'ON',
                    msg='wsrep_ready on %s is not ON' % controller,
                    failed_step='3')

                self.verify_response_body_content(
                    result.get(('wsrep_connected', 'OFF')), 'ON',
                    msg='wsrep_connected on %s is not ON' % controller,
                    failed_step='3')
        else:
            self.skipTest('There is no CentOs deployment')

    def test_state_of_galera_cluster_ubunta(self):
        """Check galera environment state
        Test verifies state of galera environment
        Target Service: HA mysql

        Scenario:
            1. Ssh on each controller and request state of galera node
            2. For each node check cluster size
            3. For each node check status is ready
            4. For each node check that node is connected to cluster
        Duration: 60 s.
        Deployment tags: Ubuntu
        """
        if 'Ubuntu' in self.config.compute.deployment_os:
            for controller in self.controllers:
                command = "mysql -e \"SHOW STATUS LIKE 'wsrep_%'\""
                ssh_client = SSHClient(controller, self.controller_user,
                                       key_filename=self.controller_key,
                                       timeout=100)
                output = self.verify(
                    20, ssh_client.exec_command, 1,
                    "Verification of galera cluster node status failed",
                    'get status from galera node',
                    command).splitlines()

                LOG.debug('output is %s' % output)

                mysql_vars = [
                    'wsrep_cluster_size',
                    'wsrep_ready',
                    'wsrep_connected'
                ]
                result = self.get_variables_from_output(output, mysql_vars)

                self.verify_response_body_content(
                    result.get('wsrep_cluster_size', 0),
                    str(len(self.controllers)),
                    msg='Cluster size on %s less '
                        'than controllers count' % controller,
                    failed_step='2')

                self.verify_response_body_content(
                    result.get('wsrep_ready', 'OFF'), 'ON',
                    msg='wsrep_ready on %s is not ON' % controller,
                    failed_step='3')

                self.verify_response_body_content(
                    result.get('wsrep_connected', 'OFF'), 'ON',
                    msg='wsrep_connected on %s is not ON' % controller,
                    failed_step='3')
        else:
            self.skipTest('There is no Ubuntu deployment')
