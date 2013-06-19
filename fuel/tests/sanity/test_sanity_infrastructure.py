import paramiko
from fuel.test import attr
from fuel.tests.sanity import base


class SanityInfrastructureTest(base.BaseComputeAdminTest):
    _interface = 'json'

    @attr(type=['sanity', 'fuel'])
    def test_services_state(self):
        list_of_expected_services = self.config.compute.enabled_services
        hostname = self.config.compute.controller_node
        port = 22
        username = self.config.compute.controller_node_ssh_user
        password = self.config.compute.controller_node_ssh_password
        sshClient = paramiko.SSHClient()
        sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            sshClient.connect(hostname, port, username, password)
            _, out, err = sshClient.exec_command("nova-manage service list")
            out = out.readlines()
            err = err.readlines()
        except BaseException:
            raise
        finally:
            sshClient.close()
        self.assertEqual("[]",
                         str(err),
                         ("nova-manage service list command has "
                          "finished with the following error %s") % err)
        self.assertFalse(u'XXX' in out)
        self.assertEqual(len(list_of_expected_services),
                         str(out).count(u':-)'),
                         'Not all the expected services started')