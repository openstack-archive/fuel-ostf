from fuel_health.common.ssh import Client as SSHClient
from fuel_health.exceptions import SSHExecCommandFailed
from fuel_health.test import attr
from fuel_health.test import ExecutionTimeout
from fuel_health.tests.sanity import base


class SanityInfrastructureTest(base.BaseComputeAdminTest):
    """
    TestClass contains tests check the whole OpenStack availability.
    Special requirements:
            1. A controller's IP should be specified in
                controller_node parameter of the config file.
            2. The controller's domain name should be specified in
                controller_node_name parameter of the config file.
            3. SSH user credentials should be specified in
                controller_node_ssh_user/password parameters
                of the config file.
            4. List of services are expected to be run should be specified in
                enabled_services parameter of the config file.
    """
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        cls.list_of_expected_services = cls.config.compute.enabled_services
        cls.host = cls.config.compute.controller_node
        cls.usr = cls.config.compute.controller_node_ssh_user
        cls.pwd = cls.config.compute.controller_node_ssh_password
        cls.hostname = cls.config.compute.controller_node_name

    @classmethod
    def tearDownClass(cls):
        pass

    @attr(type=['sanity', 'fuel'])
    def test_services_state(self):
        """
        Test all the expected services are on.
        Target component: OpenStack
        Special requirements:
            1. A controller's IP should be specified in
                controller_node parameter of the config file.
            2. SSH user credentials should be specified in
                controller_node_ssh_user/password parameters
                of the config file.
            3. List of services are expected to be run should be specified in
                enabled_services parameter of the config file.

        Scenario:
            1. Connect to a controller node via SSH.
            2. Execute nova-manage service list command.
            3. Check there is no failed services (with XXX state)
                in the command output.
            4. Check number of normally executed services (with :-) state
                is equal to the number of expected services
        """
        with ExecutionTimeout(5):
            output = SSHClient(self.host, self.usr, self.pwd).exec_command(
                "nova-manage service list")
        self.assertFalse(u'XXX' in output)
        self.assertEqual(len(self.list_of_expected_services),
                         output.count(u':-)'),
                         'Not all the expected services started')

    @attr(type=['sanity', 'fuel'])
    def test_dns_state(self):
        """
        Test all the expected services are on.
        Target component: OpenStack
        Special requirements:
            1. A controller's IP should be specified in
                controller_node parameter of the config file.
            2. The controller's domain name should be specified in
                controller_node_name parameter of the config file.
            3. The controller SSH user credentials should be specified in
                controller_node_ssh_user/password parameters
                of the config file.

        Scenario:
            1. Connect to a controller node via SSH.
            2. Execute host command for the controller IP.
            3. Check expected controller's domain name is present
                in the command output to be sure the domain name
                was successfully resolved.
        """
        output = ''
        expected_output = "in-addr.arpa domain name pointer " + self.hostname
        with ExecutionTimeout(10):
            try:
                output = SSHClient(self.host, self.usr, self.pwd).exec_command(
                    "host " + self.host)
            except SSHExecCommandFailed:
                output = "'host' command failed."
        self.assertTrue(expected_output in output,
                        'DNS name cannot be resolved')
