import logging
import paramiko
import pprint
import unittest2

from sanity_config import SanityConf

logger = logging.getLogger('paramiko.transport')
logger.setLevel(logging.ERROR)


class ResourceChecker():
    def __init__(self, ip, username, password=None, key=None):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ip_address = ip
        username = username
        password = password
        key_file = key
        self.ssh.connect(hostname=ip_address,
                         username=username,
                         password=password,
                         key_filename=key_file)

    def __del__(self):
        self.ssh.close()

    def checkFile(self, filename):
        command = 'test -e %s && echo "Found" || echo "Not found"'
        _, stdout, _ = self.ssh.exec_command(command
                                             % str(filename))
        existence = stdout.read().splitlines()
        return "Found" in existence

    def checkPackage(self, package):
        command = 'dpkg -l | grep -i %s'
        _, stdout, _ = self.ssh.exec_command(command
                                             % str(package))
        existence = stdout.read().splitlines()
        return len(existence) > 0

    def checkService(self, service):
        command = 'ps ax | grep %s | grep -v grep &>/dev/null'\
                  ' && echo "OK" || echo "FAIL"'
        _, stdout, _ = self.ssh.exec_command(command
                                             % str(service))
        existence = stdout.read().splitlines()
        return "OK" in existence


class SanityCheck(unittest2.TestCase):
    @classmethod
    def setUpClass(cls):
        conf = SanityConf()
        cls.controller_resources = conf.cont_res
        cls.compute_resources = conf.comp_res
        cls.quantum_resources = conf.quantum_res

        cls.environment = conf.environment
        cls.username = conf.username
        cls.password = conf.password
        cls.ssh_key = conf.ssh_key

    def check_node(self, node, resources):
        failed_resources = []
        check = ResourceChecker(ip=node,
                                username=self.username,
                                password=self.password,
                                key=self.ssh_key)
        for i in resources['file']:
            if not check.checkFile(i):
                failed_resources.append('%s: %s' % ('file', i))
        for i in resources['package']:
            if not check.checkPackage(i):
                failed_resources.append('%s: %s' % ('package', i))
        for i in resources['service']:
            if not check.checkService(i):
                failed_resources.append('%s: %s' % ('service', i))
        return failed_resources

    def test_controller_nodes(self):
        failed = []
        for node in self.environment['controller']:
            failed_resources = self.check_node(node, self.controller_resources)
            if failed_resources:
                failed.append({node: failed_resources})

        self.assertTrue(failed == [], "Checking of following resources failed: " +
                                      pprint.pformat(failed))

    # def test_compute_nodes(self):
    #     failed = []
    #     for node in self.environment['compute']:
    #         failed_resources = self.check_node(node, self.compute_resources)
    #         if failed_resources:
    #             failed.append({node: failed_resources})
    #
    #     self.assertTrue(failed == [], "Checking of following resources failed: " +
    #                                   pprint.pformat(failed))
    #
    # def test_quantum_nodes(self):
    #     failed = []
    #     for node in self.environment['quantum']:
    #         failed_resources = self.check_node(node, self.quantum_resources)
    #         if failed_resources:
    #             failed.append({node: failed_resources})
    #
    #     self.assertTrue(failed == [], "Checking of following resources failed: " +
    #                                   pprint.pformat(failed))
