from operator import eq
from nose.plugins.attrib import attr
from nose.tools import timed

from fuel_health.common.amqp_client import AmqpClient, AmqpEx
from fuel_health.common.ssh import Client as SSHClient
from fuel_health.common.utils.data_utils import rand_name, rand_int_id
from fuel_health.exceptions import SSHExecCommandFailed
from fuel_health.test import BaseTestCase



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
        cls._clients = {}
        cls._queue = ''
        cls._controllers = cls.config.compute.controller_nodes
        cls._usr = cls.config.compute.controller_node_ssh_user
        cls._pwd = cls.config.compute.controller_node_ssh_password
        cls._key = cls.config.compute.controller_node_ssh_key_path
        cls._ssh_timeout = cls.config.compute.ssh_timeout
        cls._queue = rand_name('ost1_test-test-queue')
        cls._rabbit_user = rand_name('ost1_testrabbitmquser')
        cls._rabbit_password = cls._rabbit_user
        cls._amqp_clients = []
        cls._rabbit_user_exists = False

    # def setUp(self):
    #     super(RabbitSmokeTest, self).setUp()
    #     if self._rabbit_user and self._rabbit_password:
    #         self._createRabbitUser(self._rabbit_user, self._rabbit_password,
    #                               self._rabbit_user_exists)

    # def tearDown(self):
    #     try:
    #         if self._queue:
    #             for client in self._amqp_clients:
    #                 client['client'].close(self._queue)
    #     except:
    #         pass
    #
    #     self._deleteRabbitUser(self._rabbit_user)
    #     super(RabbitSmokeTest, self).tearDown()

    @attr(type=['fuel', 'ha', 'non-destructive'])
    @timed(60.0)
    def test_rabbitmqctl_status(self):
        """Test verifies RabbitMQ has proper cluster structure
         is available from all the controllers"""

        cmd = 'sudo rabbitmqctl cluster_status'
        nodes = []
        for node in self._controllers:
            output = ''
            error = ''
            try:
                output = self._format_output(SSHClient(host=node,
                                   username=self._usr,
                                   password=self._pwd,
                                   pkey=self._key,
                                   timeout=self._ssh_timeout).exec_command(
                    cmd))
            except SSHExecCommandFailed as exc:
                self.fail(("Cannot get cluster status for %s node. "
                           "The following error occurs: " % node) +
                          exc._error_string)

            nodes.append({'controller': node, 'clusters': output})
        #for HA configuration number of controllers and
        #number of clusters should be the same
        _num_of_controllers = len(self._controllers)
        _aux_node_clusters = sorted(nodes[0]['clusters'])
        for node in nodes[1:]:
            self.assertEqual(_num_of_controllers, len(node["clusters"]),
                             'The number of clusters for node %s is not equal '
                             'to number of controllers' % node['controller'])

            self.assertTrue(map(eq, sorted(node['clusters']),
                                _aux_node_clusters), "Cluster lists on nodes %s"
                                                     " and %s are different" %
                                                     (nodes[0]["controller"],
                                                      node["controller"]))

    @attr(type=['fuel', 'ha', 'non-destructive'])
    @timed(60.0)
    def test_rabbit_queues(self):
        """Test verifies RabbitMQ has proper queue list
         are available from all the controllers"""
        cmd = 'sudo rabbitmqctl list_queues'
        temp_set = set()
        get_name = lambda x: x.split('\t')[0]
        for node in self._controllers:
            try:
                output = SSHClient(host=node,
                                   username=self._usr,
                                   password=self._pwd,
                                   pkey=self._key,
                                   timeout=self._ssh_timeout).exec_command(
                    cmd).splitlines()
            except SSHExecCommandFailed as exc:
                self.fail(("Cannot get queue list for %s node. "
                           "The following error occurs: " % node) +
                          exc._error_string)
            output = [get_name(x) for x in output[1:-1]]
            output = set(output)
            if len(temp_set) == 0:
                #this means it is the first node,
                #this case we check there are queues only
                temp_set = output
                self.assertTrue(len(output), "Queue list for %s controller is empty" % node)
                continue
            #check all the queues are present on all the nodes
            self.assertEqual(len(output.symmetric_difference(temp_set)), 0,
                             "Queue lists are different for %s and %s "
                             "controllers" % (self._controllers[0], node))

    def test_rabbit_ha_messages(self):
        """Test verifies all brokers RabbitMQ receive a message
         has been sent"""

        #this action needs for the following test steps
        #the only reason why it is not in setUp is that this one
        #is needed just for this test and will slow others
        self._createRabbitUser(self._rabbit_user, self._rabbit_password,
                                   self._rabbit_user_exists)

        message = 'ost1_test-test-message-' + str(rand_int_id(100000, 999999))

        for controller in self._controllers:
            amqp_client = None
            try:
                amqp_client = AmqpClient(host=controller,
                                     rabbit_username=self._rabbit_user,
                                     rabbit_password=self._rabbit_password)

            except AmqpEx.AMQPConnectionError:
                self.fail("Can not create AMQP Client for %s controller" %
                      controller)
            self._amqp_clients.append({'controller': controller, 'client': amqp_client})

        try:
            self._amqp_clients[0]['client'].create_queue(self._queue)
        except AmqpEx.AMQPConnectionError:
            self.fail("Cannot create queue %s on %s controller" %
                      (self._queue, self._amqp_clients[0]['controller']))

        for controller in self._amqp_clients:
            try:
                controller['client'].send_message(self._queue, message)
            except AmqpEx.AMQPConnectionError:
                self.fail("Cannot send message to %s" % controller)

        for controller in self._amqp_clients:
            try:
                out_mes = controller['client'].receive_message(self._queue)
                print out_mes
            except AmqpEx.AMQPConnectionError:
                self.fail("Cannot receive message from %s controller" % controller['controller'])

        try:
            if self._queue:
                for client in self._amqp_clients:
                    client['client'].close(self._queue)
        except AmqpEx.AMQPConnectionError:
            self.fail("Cannot delete queue %s on %s controller" %
                      (self._queue, self._amqp_clients[0]['controller']))

        self._deleteRabbitUser(self._rabbit_user)
        super(RabbitSmokeTest, self).tearDown()

        self.assertEqual(out_mes, message,
                             "Received message is different "
                             "from the one has been sent")


    def _format_output(self, output):
            """
            Internal function allows remove all the not valuable chars
            from the output
            """
            output = output.split('running_nodes,')[-1].split('...done.')[0]
            for char in ' {[]}\n\r':
                output = output.replace(char, '')
            return output.split(',')

    def _createRabbitUser(self, username, password, flag=False):
        if flag:
            return
        cmd = 'sudo rabbitmqctl add_user %s %s; ' \
              'sudo rabbitmqctl set_permissions %s' % \
              (username, password, username + ' ".*" ".*" ".*"')
        try:
            SSHClient(host=self._controllers[0],
                    username=self._usr,
                    password=self._pwd,
                    pkey=self._key,
                    timeout=self._ssh_timeout).exec_command(cmd)
        except SSHExecCommandFailed as exc:
            self.fail(("Cannot create RabbitMQ user %s. The following error "
                       "occurs: " % username) + exc._error_string)

    def _deleteRabbitUser(self, username):
        cmd = 'sudo rabbitmqctl delete_user %s' % (username)
        try:
            SSHClient(host=self._controllers[0],
                    username=self._usr,
                    password=self._pwd,
                    pkey=self._key,
                    timeout=self._ssh_timeout).exec_command(cmd)
        except SSHExecCommandFailed:
            pass