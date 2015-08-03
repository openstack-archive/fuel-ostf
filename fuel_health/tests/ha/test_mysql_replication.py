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
import traceback

from fuel_health.common.ssh import Client as SSHClient
from fuel_health.common.utils import data_utils
from fuel_health.tests.ha.test_mysql_status import BaseMysqlTest

LOG = logging.getLogger(__name__)


class TestMysqlReplication(BaseMysqlTest):
    @classmethod
    def setUpClass(cls):
        super(TestMysqlReplication, cls).setUpClass()
        cls.database = 'ost1' + str(data_utils.rand_int_id(100, 999))
        cls.master_ip = None

    def setUp(self):
        super(TestMysqlReplication, self).setUp()
        if 'ha' not in self.config.compute.deployment_mode:
            self.skipTest('Cluster is not HA mode, skipping tests')

    @classmethod
    def tearDownClass(cls):
        if cls.master_ip:
            try:
                cmd = "mysql -h localhost -e 'DROP DATABASE %s'" % cls.database
                SSHClient(cls.master_ip, cls.node_user,
                          key_filename=cls.node_key).exec_command(cmd)
            except Exception:
                LOG.debug(traceback.format_exc())

    def test_mysql_replication(self):
        """Check data replication over mysql
        Target Service: HA mysql

        Scenario:
            1. Check that mysql is running on all controller or database nodes.
            2. Create database on one node.
            3. Create table in created database
            4. Insert data to the created table
            5. Get replicated data from each database node.
            6. Verify that replicated data in the same from each database
            7. Drop created database
        Duration: 10 s.
        """
        LOG.info("'Test MySQL replication' started")
        databases = self.verify(20, self.get_database_nodes,
                                1, "Can not get database hostnames. Check that"
                                   " at least one controller is in operation",
                                "get database nodes",
                                self.controller_ip,
                                self.node_user,
                                key=self.node_key)

        if len(databases) == 1:
            self.skipTest('There is only one database online. '
                          'Nothing to check')

        LOG.info("Database nodes are " + ", ".join(databases))
        self.master_ip = databases[0]

        # check that mysql is running on all hosts
        cmd = 'mysql -h localhost -e "" '
        for db_node in databases:
            ssh_client = SSHClient(
                db_node, self.node_user,
                key_filename=self.node_key, timeout=100)
            self.verify(
                20, ssh_client.exec_command, 1,
                'Can not connect to mysql. '
                'Please check that mysql is running and there '
                'is connectivity by management network',
                'detect mysql node', cmd)

        database_name = self.database
        table_name = 'ost' + str(data_utils.rand_int_id(100, 999))
        record_data = str(data_utils.rand_int_id(1000000000, 9999999999))

        create_database = (
            'mysql -h localhost -e "CREATE DATABASE IF NOT EXISTS '
            '{database}" '.format(database=database_name)
        )

        create_table = (
            'mysql -h localhost -e'
            ' "CREATE TABLE IF NOT EXISTS {database}.{table}'
            ' (data VARCHAR(100))" '.format(database=database_name,
                                            table=table_name)
        )

        create_record = (
            'mysql -h localhost -e "INSERT INTO {database}.{table} (data) '
            'VALUES({data})" '.format(database=database_name,
                                      table=table_name,
                                      data=record_data)
        )

        get_record = (
            'mysql -h localhost -e "SELECT * FROM {database}.{table} '
            'WHERE data = \"{data}\"" '.format(database=database_name,
                                               table=table_name,
                                               data=record_data)
        )

        drop_db = "mysql -h localhost -e 'DROP DATABASE {database}'".format(
            database=database_name
        )

        # create db, table, insert data on one node
        LOG.info('target node ip/hostname: "{0}" '.format(self.master_ip))
        master_ssh_client = SSHClient(self.master_ip, self.node_user,
                                      key_filename=self.node_key,
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

        # Verify that data is replicated on other databases
        for db_node in databases:
            if db_node != self.master_ip:
                client = SSHClient(db_node,
                                   self.node_user,
                                   key_filename=self.node_key)

                output = self.verify(
                    20, client.exec_command, 5,
                    'Can not get data from database node %s' % db_node,
                    'get_record', get_record)

                self.verify_response_body(output, record_data,
                                          msg='Expected data missing',
                                          failed_step='6')

        # Drop created db
        ssh_client = SSHClient(self.master_ip, self.node_user,
                               key_filename=self.node_key)
        self.verify(20, ssh_client.exec_command, 7,
                    'Can not delete created database',
                    'database deletion', drop_db)
        self.master_ip = None
