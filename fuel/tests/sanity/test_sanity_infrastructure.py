from fuel.common.ssh import Client as SSHClient
from fuel.test import attr
from fuel.tests.sanity import base


class SanityInfrastructureTest(base.BaseComputeAdminTest):
    _interface = 'json'

    @attr(type=['sanity', 'fuel'])
    def test_services_state(self):
        list_of_expected_services = self.config.compute.enabled_services
        host = self.config.compute.controller_node
        usr = self.config.compute.controller_node_ssh_user
        pwd = self.config.compute.controller_node_ssh_password
        output = SSHClient(host, usr, pwd).exec_command(
            "nova-manage service list")
        self.assertFalse(u'XXX' in output)
        self.assertEqual(len(list_of_expected_services),
                         output.count(u':-)'),
                         'Not all the expected services started')
