import logging
from operator import eq
from nose.plugins.attrib import attr

from fuel_health import config
from fuel_health.common.amqp_client import RabbitClient
from fuel_health.common.ssh import Client as SSHClient
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
        cls.amqp_clients = [RabbitClient(cnt,
                                         cls._usr,
                                         cls._pwd, cls._key,
                                         cls._ssh_timeout,
                                         cls._rabbit_user,
                                         cls._rabbit_password)
                            for cnt in cls._controllers]

    @attr(type=['fuel', 'ha', 'non-destructive'])
    def test_rabbitmqctl_status(self):
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
    def test_rabbit_queues(self):
        """RabbitMQ queues availability
        Scenario:
          1. Retrieve list of RabbitMQ queues for each controller
          2. Check the same queue list is present on each node
        Duration: 100
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
                self.assertTrue(output, "Step 2 failed: Queue list for %s"
                                        " controller is empty" % node)
                continue
                #check all the queues are present on all the nodes
            self.assertFalse(output.symmetric_difference(temp_set),
                             "Step 2 failed: Queue lists are different for %s "
                             "and %s controllers" %
                             (self._controllers[0], node))

    @attr(type=['fuel', 'ha', 'non-destructive'])
    def test_rabbit_messages(self):
        """RabbitMQ messages availability
        Scenario:
          1. Create a queue on one of the controllers
          2. Check the same queue is available on each the controller
          3. Publish message to the queue.
          4. Check the message is available on other controllers
        Duration: 100
        """
        if not self._controllers:
            self.fail('Step 1 failed: There are no controller nodes.')

        self.fail(self.amqp_clients[0].list_queues())

    def _format_output(self, output):
        """
        Internal function allows remove all the not valuable chars
        from the output
        """
        output = output.split('running_nodes,')[-1].split('...done.')[0]
        for char in ' {[]}\n\r':
            output = output.replace(char, '')
        return output.split(',')
