from fuel.common.ssh import Client as SSHClient
from fuel.test import attr
from fuel.tests.sanity import base


class SanityInfrastructureTest(base.BaseComputeAdminTest):
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
        output = SSHClient(self.host, self.usr, self.pwd).exec_command(
            "nova-manage service list")
        self.assertFalse(u'XXX' in output)
        self.assertEqual(len(self.list_of_expected_services),
                         output.count(u':-)'),
                         'Not all the expected services started')

    @attr(type=['sanity', 'fuel'])
    def test_dns_state(self):
        output = ''
        try:
            output = SSHClient(self.host, self.usr, self.pwd).exec_command(
                "host " + self.host)
        finally:
            expected_output = 'in-addr.arpa domain name pointer ' + \
                              self.hostname
            self.assertTrue(expected_output in output,
                            'DNS name cannot be resolved')
