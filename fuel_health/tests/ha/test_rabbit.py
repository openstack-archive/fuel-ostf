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

import fuel_health
import fuel_health.common.amqp_client
import fuel_health.common.utils.data_utils
from fuel_health.test import BaseTestCase


LOG = logging.getLogger(__name__)


class RabbitSmokeTest(BaseTestCase):
    """
    TestClass contains RabbitMQ test checks.
    """

    @classmethod
    def setUpClass(cls):
        cls.config = fuel_health.config.FuelConfig()
        cls._controllers = cls.config.compute.controller_nodes
        cls._usr = cls.config.compute.controller_node_ssh_user
        cls._pwd = cls.config.compute.controller_node_ssh_password
        cls._key = cls.config.compute.path_to_private_key
        cls._ssh_timeout = cls.config.compute.ssh_timeout
        cls.amqp_pwd = cls.config.compute.amqp_pwd
        cls.amqp_clients = [fuel_health.common.amqp_client.RabbitClient(
            cnt,
            cls._usr,
            cls._key,
            cls._ssh_timeout,
            rabbit_username='nova',
            rabbit_password=cls.amqp_pwd) for cnt in cls._controllers]

    def setUp(self):
        super(RabbitSmokeTest, self).setUp()
        if 'ha' not in self.config.mode:
            self.fail("It is not HA configuration")
        if not self._controllers:
            self.fail('There are no controller nodes')
        if not self.amqp_clients:
            self.fail('Cannot create AMQP clients for controllers')
        if len(self._controllers) == 1:
            self.fail('There is only one controller online')

    def test_001_rabbitmqctl_status(self):
        """Check RabbitMQ is available

        Scenario:
          1. Retrieve cluster status for each controller.
          2. Check that numbers of rabbit nodes is the same as controllers.
        Duration: 100 s.
        Deployment tags: CENTOS
        """
        first_list = self.verify(10, self.amqp_clients[0].list_nodes, 1,
                                 'Cannot retrieve cluster nodes'
                                 ' list for {ctlr} controller.'.format(
                                     ctlr=self.amqp_clients[0].host))

        if len(self._controllers) != self.amqp_clients[0].list_nodes():
            self.fail('Step 2 failed: Number of controllers is not equal to '
                      'number of cluster nodes.')

    def test_002_rabbitmqctl_status_ubuntu(self):
        """RabbitMQ availability
        Scenario:
          1. Retrieve cluster status for each controller.
          2. Check that numbers of rabbit nodes is the same as controllers.
        Duration: 100 s.
        Deployment tags: Ubuntu
        """
        first_list = self.verify(10, self.amqp_clients[0].list_nodes, 1,
                                 'Cannot retrieve cluster nodes'
                                 ' list for {ctlr} controller.'.format(
                                     ctlr=self.amqp_clients[0].host))

        if len(self._controllers) != self.amqp_clients[0].list_nodes():
            self.fail('Step 2 failed: Number of controllers is not equal to '
                      'number of cluster nodes.')
