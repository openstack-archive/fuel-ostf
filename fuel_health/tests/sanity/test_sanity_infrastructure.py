from fuel_health.common.ssh import Client as SSHClient
from fuel_health.exceptions import SSHExecCommandFailed
from nose.plugins.attrib import attr

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
        cls.key = cls.config.compute.controller_node_ssh_key_path
        cls.hostname = cls.config.compute.controller_node_name

    @classmethod
    def tearDownClass(cls):
        pass

    @attr(type=['sanity', 'fuel'])
    def test_services_state(self):
        """Test all of the expected services are on."""
        output_msg = ''
        try:
            output = SSHClient(self.host, self.usr, self.pwd,
                               pkey=self.key).exec_command('nova-manage '
                                                           'service list')
        except SSHExecCommandFailed:
            output_msg = "Error: 'nova-manage' command execution failed."

        output_msg = output_msg or ('Some service has not been started:' +
                                    str(self.list_of_expected_services))
        self.assertFalse(u'XXX' in output, output_msg)
        self.assertTrue(len(self.list_of_expected_services) <=
                         output.count(u':-)'),
                         output_msg)

    @attr(type=['sanity', 'fuel'])
    def test_dns_state(self):
        """Test dns is available."""
        expected_output = "in-addr.arpa domain name pointer " + self.hostname
        try:
            output = SSHClient(self.host, self.usr, self.pwd,
                               pkey=self.key).exec_command("host " + self.host)
        except SSHExecCommandFailed:
            output = "'host' command failed."
        self.assertTrue(expected_output in output,
                        'DNS name cannot be resolved')
