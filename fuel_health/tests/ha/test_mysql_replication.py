# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Mirantis, Inc.
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
from fuel_health.common.utils import data_utils
from fuel_health import nmanager


LOG = logging.getLogger(__name__)


class TestMysqlReplication(nmanager.OfficialClientTest):
    @classmethod
    def setUpClass(cls):
        super(TestMysqlReplication, cls).setUpClass()
        cls.controller_ip = cls.config.compute.controller_nodes[0]
        cls.controllers = cls.config.compute.controller_nodes
        cls.controller_key = cls.config.compute.path_to_private_key
        cls.controller_user = cls.config.compute.ssh_user
        cls.mysql_user = 'root'
        cls.database = 'ost1' + str(data_utils.rand_int_id(100, 999))
        cls.master_ip = []

    def setUp(self):
        super(TestMysqlReplication, self).setUp()
        if 'ha' not in self.config.compute.deployment_mode:
            self.fail('Cluster is not HA mode, skipping tests')

    @classmethod
    def tearDownClass(cls):
        if cls.master_ip:
            try:
                cmd = "mysql -e 'DROP DATABASE %s'" % cls.database

                SSHClient(cls.master_ip[0], cls.controller_user,
                          key_filename=cls.controller_key).exec_command(cmd)
            except Exception as e:
                LOG.debug(e)
                pass

    def test_mysql_replication(self):
        """Check data replication over mysql
        Test checks that data replication happens in HA mode.
        Target Service: HA mysql
        Scenario:
            1. Detect mysql node.
            2. Create database on detected node
            3. Create table in created database
            4. Insert data to the created table
            5. Get replicated data from each controller.
            6. Verify that replicated data in the same from each controller
            7. Drop created database
        Duration: 1-40 s.
        """
        # Find mysql master node
        master_node_ip = []
        cmd = 'mysql -e "SHOW SLAVE STATUS\G"'
        LOG.info("Controllers nodes are %s" % self.controllers)
        for controller_ip in self.controllers:
            ssh_client = SSHClient(
                controller_ip, self.controller_user,
                key_filename=self.controller_key, timeout=100)
            output = self.verify(
                20, ssh_client.exec_command, 1, 'Mysql node detection failed',
                'detect mysql node', cmd)
            LOG.info('output is %s' % output)
            if not output:
                self.master_ip.append(controller_ip)
                master_node_ip.append(controller_ip)

        database_name = self.database
        table_name = 'ost' + str(data_utils.rand_int_id(100, 999))
        record_data = str(data_utils.rand_int_id(1000000000, 9999999999))

        create_database = 'mysql -e "CREATE DATABASE IF NOT EXISTS %s"'\
                          % database_name
        create_table = 'mysql -e "CREATE TABLE IF NOT EXISTS'\
                       ' %(database)s.%(table)s'\
                       ' (data VARCHAR(100))"'\
                       % {'database': database_name,
                          'table': table_name}
        create_record = 'mysql -e "INSERT INTO %(database)s.%(table)s (data)'\
                        ' VALUES(%(data)s)"'\
                        % {'database': database_name,
                            'table': table_name,
                            'data': record_data}
        get_record = 'mysql -e "SELECT * FROM %(database)s.%(table)s '\
                     'WHERE data = \"%(data)s\""'\
                     % {'database': database_name,
                        'table': table_name,
                        'data': record_data}

        # create db, table, insert data on master
        LOG.info('master node ip %s' % master_node_ip[0])
        master_ssh_client = SSHClient(master_node_ip[0], self.controller_user,
                                      key_filename=self.controller_key,
                                      timeout=100)

        self.verify(20, master_ssh_client.exec_command, 2,
                    'Database creation failed', 'create database',
                    create_database)
        LOG.info('create database')
        self.verify(20, master_ssh_client.exec_command, 3,
                    'Table creation failed', 'create table', create_table)
        LOG.info('create table')
        self.verify(20, master_ssh_client.exec_command, 4,
                    'Can not insert data in created table', 'data insertion',
                    create_record)
        LOG.info('create data')

        # Verify that data is replicated on other controllers
        for controller in self.controllers:
            if controller not in master_node_ip:
                client = SSHClient(controller,
                                   self.controller_user,
                                   key_filename=self.controller_key)
                result = []
                output = self.verify(
                    20, client.exec_command, 5,
                    'Can not get data from controller %s' % controller,
                    'get_record', get_record)

                result.append(output)
                try:
                    res = result[0].splitlines()[-1]

                except IndexError:
                    res = ''

                self.verify_response_body_content(
                    record_data, res, msg='Expected data missing',
                    failed_step='6')

        # Drop created db
        cmd = "mysql -e 'DROP DATABASE %s'" % self.database
        ssh_client = SSHClient(master_node_ip[0], self.controller_user,
                               key_filename=self.controller_key)
        self.verify(20, ssh_client.exec_command, 7,
                    'Can not delete created database',
                    'database deletion', cmd)

    def test_os_databases(self):
        """Check amount of tables in os databases is the same on each node
        Test checks amount of os databases and tables on each node
        Target Service: HA mysql
        Scenario:
            1. Request list of tables for os databases on each node.
            2. Check that amount of tables for each database is the same
        Duration: 1-40 s.
        """
        dbs = ['nova', 'glance', 'keystone']
        cmd = "mysql -e 'SHOW TABLES FROM %(database)s'"
        for database in dbs:
            LOG.info('Current database name is %s' % database)
            temp_set = set()
            for node in self.config.compute.controller_nodes:
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
        """Check mysql cluster state
        Test verifies state of mysql cluster
        Target Service: HA mysql
        Scenario:
            1. Detect mysql master node.
            2. Ssh on mysql-master node and request its status
            3. Verify that position field is not empty
            4. Ssh on mysql-slave nodes and request their statuses
            5. Verify that  Slave_IO_State is in appropriate state
            6. Verify that Slave_IO_Running is in appropriate state
            7. Verify that Slave_SQL_Running is in appropriate state
        Duration: 1-40 s.
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
                        ' Yes',  msg='Slave_IO_Running state is incorrect',
                        failed_step='6')

                    self.verify_response_body(
                        slave_dict['Slave_SQL_Running'],
                        ' Yes',  msg='Slave_SQL_Running state is incorrect',
                        failed_step='7')
        else:
            self.fail("There is no RHEL deployment")

    def test_state_of_galera_cluster(self):
        """Check galera cluster state
        Test verifies state of galera cluster
        Target Service: HA mysql

        Scenario:
            1. Ssh on each controller and request state of galera node
            2. For each node check cluster size
            3. For each node check status is ready
            4. For each node check that node is connected to cluster
        Duration: 1-20 s.
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
                        command).splitlines()[3:-2]

                    LOG.debug('output is %s' % output)

                    result = {}
                    for i in output:
                        key, value = i.split('|')[0:-2]
                        result.update({key: value})
                        return result

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
            self.fail('There is no CentOs deployment')
