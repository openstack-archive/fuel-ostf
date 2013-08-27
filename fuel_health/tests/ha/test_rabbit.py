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
    TestClass contains tests check RabbitMQ.
    """

    @classmethod
    def setUpClass(cls):
        cls.config = fuel_health.config.FuelConfig()
        cls._controllers = cls.config.compute.controller_nodes
        cls._usr = cls.config.compute.controller_node_ssh_user
        cls._pwd = cls.config.compute.controller_node_ssh_password
        cls._key = cls.config.compute.path_to_private_key
        cls._ssh_timeout = cls.config.compute.ssh_timeout
        cls.amqp_clients = [fuel_health.common.amqp_client.RabbitClient(
            cnt,
            cls._usr,
            cls._pwd,
            cls._key,
            cls._ssh_timeout) for cnt in cls._controllers]

    def setUp(self):
        super(RabbitSmokeTest, self).setUp()
        if self.config.mode != 'ha':
            self.fail("It is not HA configuration")
        if not self._controllers:
            self.fail('There are no compute nodes')
        if not self.amqp_clients:
            self.fail('Cannot create AMQP clients for controllers')

    def test_001_rabbitmqctl_status(self):
        """RabbitMQ cluster availability

        Scenario:
          1. Retrieve cluster status for each the controller.
          2. Check number of clusters are equal to number of controllers.
          3. Check cluster list is the same for each the controller.
        Duration: 100 s.
        """
        first_list = self.verify(10, self.amqp_clients[0].list_nodes, 1,
                                 'Cannot retrieve cluster nodes'
                                 ' list for {ctlr} controller.'.format(
                                     ctlr=self.amqp_clients[0].host))
        if not first_list:
            self.fail('Step 1 failed: Cannot retrieve cluster nodes list for '
                      '{ctlr} controller.'.
                      format(ctlr=self.amqp_clients[0].host))
        if len(self._controllers) != len(eval(first_list)):
            self.fail('Step 2 failed: Number of controllers is not equal to '
                      'number of cluster nodes.')

        for client in self.amqp_clients[1:]:
            list = self.verify(10, client.list_nodes, 1,
                               'Cannot retrieve cluster nodes'
                               ' list for {ctlr} controller.'.format(
                                   ctlr=client.host))
            if not list:
                self.fail('Step 1 failed: Cannot retrieve cluster nodes list '
                          'for {ctlr} controller.'.format(ctlr=client.host))
            if list != first_list:
                self.fail('Step 3 failed: Cluster nodes lists for controllers '
                          '{ctlr1} and {ctlr2} are different.'.format(
                          ctlr1=client.host,
                          ctlr2=self.amqp_clients[0].host))

    def test_002_rabbit_queues(self):
        """RabbitMQ queues availability
        Scenario:
          1. Retrieve list of RabbitMQ queues for each controller
          2. Check the same queue list is present on each node
        Duration: 100 s.
        """
        first_list = self.verify(10, self.amqp_clients[0].list_queues,
                                 1,
                                 'Cannot retrieve queues list for {ctlr} '
                                 'controller.'.format(
                                     ctlr=self.amqp_clients[0].host))
        if not first_list:
                self.fail('Step 1 failed: Cannot retrieve queues list for '
                          '{ctlr} controller.'.format(
                          ctlr=self.amqp_clients[0].host))
        for client in self.amqp_clients[1:]:
            list = self.verify(10, client.list_queues,
                               1,
                               'Cannot retrieve queues list for {ctlr} '
                               'controller.'.format(ctlr=client.host))
            if not list:
                self.fail('Step 1 failed: Cannot retrieve queues list for '
                          '{ctlr} controller.'.format(ctlr=client.host))
            if list != first_list:
                self.fail('Step 2 failed: Queue lists for controllers {ctlr1}'
                          ' and {ctlr2} are different.'.format(
                          ctlr1=client.host,
                          ctlr2=self.amqp_clients[0].host))

    def test_003_rabbit_messages(self):
        """RabbitMQ messages availability
        Scenario:
          1. Create a queue on a controller
          2. Create an exchange on the controller
          3. Create a binding for the queue and exchange
          4. Publish messages to the queue.
          5. Check the messages are available on other controllers
          6. Delete the exchange
          7. Delete the queue (with binding)
        Duration: 100 s.
        """
        new_queue = fuel_health.common.utils.data_utils.rand_name(
            name='ostf1-test-queue-')
        new_exchange = fuel_health.common.utils.data_utils.rand_name(
            name='ostf1-test-exchange-')
        new_binding = fuel_health.common.utils.data_utils.rand_name(
            name='ostf1-test-binding-')
        first_client = self.amqp_clients[0]
        result = self.verify(20, first_client.create_queue, 1,
                             "Cannot create queue {name}.".format(
                                 name=new_queue),
                             "Queue creation.",
                             new_queue)
        self.verify_response_true('204 No Content' in result,
                                  'Step 1 failed: {queue} queue cannot be '
                                  'created on {ctlr} controller.'.format(
                                      queue=new_queue, ctlr=first_client.host))

        result = self.verify(20, first_client.create_exchange, 2,
                             "Cannot create exchange {name}.".format(
                                 name=new_exchange),
                             "Exchange creation.",
                             new_exchange)
        self.verify_response_true('204 No Content' in result,
                                  'Step 2 failed: {ex} exchange cannot be '
                                  'created on {ctlr} controller.'.format(
                                      ex=new_exchange, ctlr=first_client.host))

        result = self.verify(20, first_client.create_binding, 3,
                             "Cannot create binding {name}.".format(
                                 name=new_binding),
                             "Binding creation.",
                             new_exchange,
                             new_queue,
                             new_binding)
        self.verify_response_true('204 No Content' in result,
                                  'Step 2 failed: {bin} binding cannot be '
                                  'created for {queue} queue and {ex} '
                                  'exchange on {ctlr} controller.'.format(
                                      ex=new_exchange, ctlr=first_client.host,
                                      bin=new_binding, queue=new_queue))

        for client in self.amqp_clients:
            result = self.verify(20, first_client.publish_message, 4,
                                 "Cannot push message.", "Message pushing.",
                                 "Test Message", new_exchange, new_binding)
            self.verify_response_true('200 OK' in result,
                                      'Step 4 failed: '
                                      'Message cannot be pushed.')
            self.verify(20, client.get_message, 5,
                        "Cannot get message.", "Message receiving.",
                        new_queue)
            self.verify_response_true('200 OK' in result,
                                      'Step 5 failed: '
                                      'Message cannot be received '
                                      'on %s controller.' %
                                      client.host)

        result = self.verify(20, first_client.delete_exchange, 6,
                             "Cannot delete exchange {name}.".format(
                                 name=new_exchange),
                             "Queue deletion.", new_exchange)
        self.verify_response_true('204 No Content' in result,
                                  'Step 6 failed: {ex} exchange cannot be '
                                  'removed on {ctlr} controller.'.format(
                                      ctlr=first_client.host, ex=new_exchange))

        result = self.verify(20, first_client.delete_queue, 7,
                             "Cannot delete queue {name}.".format(
                                 name=new_queue),
                             "Queue deletion.", new_queue)
        self.verify_response_true('204 No Content' in result,
                                  'Step 7 failed: {queue} queue cannot be '
                                  'removed on {ctlr} controller.'.format(
                                      ctlr=first_client.host, queue=new_queue))
