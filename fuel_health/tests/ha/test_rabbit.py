import logging
from nose.plugins.attrib import attr

from fuel_health import config
from fuel_health.common.amqp_client import RabbitClient
from fuel_health.common.ssh import Client as SSHClient
from fuel_health.common.utils.data_utils import rand_name
from fuel_health.test import BaseTestCase

LOG = logging.getLogger(__name__)


class RabbitSmokeTest(BaseTestCase):
    """
    TestClass contains tests check RabbitMQ.
    Special requirements:
            1. A controllers' IPs should be specified in
                controller_nodes parameter of the config file.
            2. The controllers' domain names should be specified in
                controller_nodes_name parameter of the config file.
            3. SSH user credentials should be specified in
                controller_node_ssh_user/password parameters
                of the config file.
            4. List of services are expected to be run should be specified in
                enabled_services parameter of the config file.
            5. SSH user should have root permissions on controllers
    """

    @classmethod
    def setUpClass(cls):
        cls.config = config.FuelConfig()
        if cls.config.mode != 'ha':
            cls.skipTest("It is not HA configuration")
        cls._controllers = cls.config.compute.controller_nodes
        cls._usr = cls.config.compute.controller_node_ssh_user
        cls._pwd = cls.config.compute.controller_node_ssh_password
        cls._key = cls.config.compute.path_to_private_key
        cls._ssh_timeout = cls.config.compute.ssh_timeout
        cls._rabbit_user = 'nova'
        cls._rabbit_password = 'D4ZfVmsF'
        cls.amqp_clients = [RabbitClient(cnt,
                                         cls._usr,
                                         cls._pwd, cls._key,
                                         cls._ssh_timeout,
                                         cls._rabbit_user,
                                         cls._rabbit_password)
                            for cnt in cls._controllers]

    @attr(type=['fuel', 'ha', 'non-destructive'])
    def test_001_rabbitmqctl_status(self):
        """RabbitMQ cluster availability

        Scenario:
          1. Retrieve cluster status for each the controller.
          2. Check number of clusters are equal to number of controllers.
          3. Check cluster list is the same for each the controller.
        Duration: 100 s.
        """
        if not self.amqp_clients:
            self.fail('Step 1 failed: There are no controller nodes.')
        first_list = self.amqp_clients[0].list_nodes()
        LOG.debug(first_list)
        if not first_list:
                self.fail('Step 1 failed: Cannot retrieve cluster nodes list '
                          'for {ctlr} controller.'.format(
                    ctlr=self.amqp_clients[0].host))
        LOG.debug(len(self._controllers))
        LOG.debug(len(first_list))
        if len(self._controllers) != len(eval(first_list)):
            self.fail('Step 2 failed: Number of controllers is not equal to '
                      'number of cluster nodes.')

        for client in self.amqp_clients[1:]:
            list = client.list_nodes()
            if not list:
                self.fail('Step 1 failed: Cannot retrieve cluster nodes list '
                          'for {ctlr} controller.'.format(ctlr=client.host))
            if list != first_list:
                self.fail('Step 3 failed: Cluster nodes lists for controllers '
                          '{ctlr1} and {ctlr2} are different.'.format(
                    ctlr1=client.host,
                    ctlr2=self.amqp_clients[0].host)
                )


    @attr(type=['fuel', 'ha', 'non-destructive'])
    def test_002_rabbit_queues(self):
        """RabbitMQ queues availability
        Scenario:
          1. Retrieve list of RabbitMQ queues for each controller
          2. Check the same queue list is present on each node
        Duration: 100 s.
        """
        if not self.amqp_clients:
            self.fail('Step 1 failed: There are no controller nodes.')
        first_list = self.amqp_clients[0].list_queues()
        if not first_list:
                self.fail('Step 1 failed: Cannot retrieve queues list for '
                          '{ctlr} controller.'.format(
                    ctlr=self.amqp_clients[0].host))
        for client in self.amqp_clients[1:]:
            list = client.list_queues()
            if not list:
                self.fail('Step 1 failed: Cannot retrieve queues list for '
                          '{ctlr} controller.'.format(ctlr=client.host))
            if list != first_list:
                self.fail('Step 2 failed: Queue lists for controllers {ctlr1}'
                          ' and {ctlr2} are different.'.format(
                    ctlr1=client.host,
                    ctlr2=self.amqp_clients[0].host)
                )


    @attr(type=['fuel', 'ha', 'non-destructive'])
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
        if not self._controllers:
            self.fail('Step 1 failed: There are no controller nodes.')

        new_queue = rand_name(name='ostf1-test-queue-')
        new_exchange = rand_name(name='ostf1-test-exchange-')
        new_binding = rand_name(name='ostf1-test-binding-')
        first_client = self.amqp_clients[0]
        result = self.verify(20, first_client.create_queue, 1,
                    "Cannot create queue {name}.".format(name=new_queue),
                    "Queue creation.", new_queue)
        self.verify_response_true('204 No Content' in result,
                                  'Step 1 failed: {queue} queue cannot be '
                                  'created on {ctlr} controller.'.format(
                                      queue=new_queue, ctlr=first_client.host))

        result = self.verify(20, first_client.create_exchange, 2,
                    "Cannot create exchange {name}.".format(name=new_exchange),
                    "Exchange creation.", new_exchange)
        self.verify_response_true('204 No Content' in result,
                                  'Step 2 failed: {ex} exchange cannot be '
                                  'created on {ctlr} controller.'.format(
                                      ex=new_exchange, ctlr=first_client.host))

        result = self.verify(20, first_client.create_binding, 3,
                    "Cannot create binding {name}.".format(name=new_binding),
                    "Binding creation.", new_exchange, new_queue, new_binding)
        self.verify_response_true('204 No Content' in result,
                                  'Step 2 failed: {bin} binding cannot be '
                                  'created for {queue} queue and {ex} '
                                  'exchange on {ctlr} controller.'.format(
                                      ex=new_exchange, ctlr=first_client.host,
                                      bin=new_binding, queue=new_queue))

        client_id = 0
        for clr in self._controllers:
            result = self.verify(20, first_client.publish_message, 4,
                        "Cannot push message.", "Message pushing.",
                        "Test Message", new_exchange, new_binding)
            self.verify_response_true('200 OK' in result,
                                  'Step 4 failed: Message cannot be pushed.')
            self.verify(20, self.amqp_clients[client_id].get_message, 5,
                        "Cannot get message.", "Message receiving.",
                        new_queue)
            self.verify_response_true('200 OK' in result,
                                  'Step 5 failed: Message cannot be received '
                                  'on %s controller.' %
                                  self.amqp_clients[client_id].host)
            client_id = client_id + 1

        result = self.verify(20, first_client.delete_exchange, 6,
                    "Cannot delete exchange {name}.".format(name=new_exchange),
                    "Queue deletion.", new_exchange)
        self.verify_response_true('204 No Content' in result,
                                  'Step 6 failed: {ex} exchange cannot be '
                                  'removed on {ctlr} controller.'.format(
                                      ctlr=first_client.host, ex=new_exchange))

        result = self.verify(20, first_client.delete_queue, 7,
                    "Cannot delete queue {name}.".format(name=new_queue),
                    "Queue deletion.", new_queue)
        self.verify_response_true('204 No Content' in result,
                                  'Step 7 failed: {queue} queue cannot be '
                                  'removed on {ctlr} controller.'.format(
                                      ctlr=first_client.host, queue=new_queue))
