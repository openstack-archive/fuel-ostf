import logging
from operator import eq
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
        if not self._controllers:
            self.fail('Step 1 failed: There are no controller nodes.')
        cmd = 'sudo rabbitmqctl cluster_status'
        nodes = []
        for node in self._controllers:
            output = ''
            error = ''
            ssh_client = SSHClient(host=node, username=self._usr,
                                   password=self._pwd,
                                   pkey=self._key,
                                   timeout=self._ssh_timeout)
            output = self._format_output(self.verify(20,
                                                     ssh_client.exec_command,
                                                     1,
                                                     "Cannot get cluster "
                                                     "status for %s node." %
                                                     node,
                                                     "Retrieve cluster status "
                                                     "for each the controller",
                                                     cmd))
            nodes.append({'controller': node, 'clusters': output})
            #for HA configuration number of controllers and
        #number of clusters should be the same
        _num_of_controllers = len(self._controllers)
        _aux_node_clusters = sorted(nodes[0]['clusters'])
        for node in nodes[1:]:
            self.assertEqual(_num_of_controllers, len(node["clusters"]),
                             'Step 2 failed: The number of clusters for '
                             'node %s is not equal to number of controllers' %
                             node['controller'])

            self.assertTrue(map(eq, sorted(node['clusters']),
                                _aux_node_clusters), "Step 3 failed: Cluster "
                                                     "lists on nodes %s"
                                                     " and %s are different" %
                                                     (nodes[0]["controller"],
                                                      node["controller"]))

    @attr(type=['fuel', 'ha', 'non-destructive'])
    def test_002_rabbit_queues(self):
        """RabbitMQ queues availability
        Scenario:
          1. Retrieve list of RabbitMQ queues for each controller
          2. Check the same queue list is present on each node
        Duration: 100 s.
        """
        if not self._controllers:
            self.fail('Step 1 failed: There are no controller nodes.')
        cmd = 'sudo rabbitmqctl list_queues'
        temp_set = set()
        get_name = lambda x: x.split('\t')[0]
        for node in self._controllers:
            ssh_client = SSHClient(host=node,
                                   username=self._usr,
                                   password=self._pwd,
                                   pkey=self._key,
                                   timeout=self._ssh_timeout)
            output = self.verify(20, ssh_client.exec_command, 1,
                                 "Cannot get queue list for %s node. " % node,
                                 "Retrieve queue list",
                                 cmd)
            output = set([get_name(x) for x in (output.splitlines())[1:-1]])
            if not temp_set:
                #this means it is the first node,
                #this case we check there are queues only
                temp_set = output
                if not output:
                    self.fail("Step 2 failed: Queue list for %s"
                              " controller is empty" % node)
                continue
                #check all the queues are present on all the nodes
            if output.symmetric_difference(temp_set):
                self.fail("Step 2 failed: Queue lists are different for %s "
                          "and %s controllers" %
                          (self._controllers[0], node))

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

    def _format_output(self, output):
        """
        Internal function allows remove all the not valuable chars
        from the output
        """
        output = output.split('running_nodes,')[-1].split('...done.')[0]
        for char in ' {[]}\n\r':
            output = output.replace(char, '')
        return output.split(',')
