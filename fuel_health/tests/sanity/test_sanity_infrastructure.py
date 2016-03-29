# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import time

from fuel_health.common.ssh import Client as SSHClient
from fuel_health import nmanager

LOG = logging.getLogger(__name__)


class SanityInfrastructureTest(nmanager.SanityChecksTest):
    """TestClass contains tests that check the whole OpenStack availability.
    Special requirements:
        1. A controller's IP address should be specified.
        2. A compute's IP address should be specified.
        3. SSH user credentials for the controller and the compute
           should be specified in the controller_node_ssh_user parameter
    """

    @classmethod
    def setUpClass(cls):
        super(SanityInfrastructureTest, cls).setUpClass()
        cls.controllers = cls.config.compute.online_controllers
        cls.computes = cls.config.compute.online_computes
        cls.usr = cls.config.compute.controller_node_ssh_user
        cls.pwd = cls.config.compute.controller_node_ssh_password
        cls.key = cls.config.compute.path_to_private_key
        cls.timeout = cls.config.compute.ssh_timeout
        cls.fuel_dns = cls.config.fuel.dns

    @classmethod
    def tearDownClass(cls):
        pass

    def test_001_services_state(self):
        """Check that required services are running
        Target component: OpenStack

        Scenario:
            1. Execute nova service-list command on a controller node.
            2. Check there are no failed services (with down state).
        Duration: 180 s.
        """
        downstate = u'down'
        cmd = 'source /root/openrc; nova service-list'
        if not self.controllers:
            self.skipTest('Step 1 failed: there are no controller nodes.')
        ssh_client = SSHClient(self.controllers[0],
                               self.usr, self.pwd,
                               key_filename=self.key,
                               timeout=self.timeout)
        output = self.verify(50, ssh_client.exec_command, 1,
                             "'nova service-list' command execution failed. ",
                             "'nova service-list' command execution",
                             cmd)
        LOG.debug(output)
        try:
            self.verify_response_true(
                downstate not in output, 'Step 2 failed: Some nova services '
                'have not been started.')
        except Exception:
            LOG.info("Will sleep for 120 seconds and try again")
            LOG.exception()
            time.sleep(120)
            self.verify_response_true(
                downstate not in output, 'Step 2 failed: Some nova services '
                'have not been started.')

    def test_002_internet_connectivity_from_compute(self):
        """Check internet connectivity from a compute
        Target component: OpenStack

        Scenario:
            1. Execute ping 8.8.8.8 command from a compute node.
        Duration: 100 s.

        Deployment tags: qemu | kvm, public_on_all_nodes | nova_network
        """
        if not self.computes:
            self.skipTest('There are no compute nodes')

        cmd = "ping -q -c1 -w10 8.8.8.8"

        ssh_client = SSHClient(self.computes[0],
                               self.usr,
                               self.pwd,
                               key_filename=self.key,
                               timeout=self.timeout)
        self.verify(100, self.retry_command, 1,
                    "'ping' command failed. Looks like there is no "
                    "Internet connection on the compute node.",
                    "'ping' command",
                    2, 30, ssh_client.exec_command, cmd)

    def test_003_dns_resolution(self):
        """Check DNS resolution on compute node
        Target component: OpenStack

        Scenario:
            1. Execute host 8.8.8.8 command from a compute node.
            2. Check 8.8.8.8 host was successfully resolved
            3. Check host google.com command from the compute node.
            4. Check google.com host was successfully resolved.
        Duration: 120 s.

        Deployment tags: qemu | kvm, public_on_all_nodes | nova_network
        """
        if not self.computes:
            self.skipTest('There are no computes nodes')

        dns = self.fuel_dns.spit(',') if self.fuel_dns else ['8.8.8.8']

        ssh_client = SSHClient(self.computes[0],
                               self.usr,
                               self.pwd,
                               key_filename=self.key,
                               timeout=self.timeout)
        expected_output = "{0}.in-addr.arpa domain name pointer".format(dns[0])

        cmd = "host {0}".format(dns[0])
        output = self.verify(100, self.retry_command, 1,
                             "'host' command failed. Looks like there is no "
                             "Internet connection on the computes node.",
                             "'ping' command", 10, 5,
                             ssh_client.exec_command, cmd)
        LOG.debug(output)
        self.verify_response_true(expected_output in output,
                                  'Step 2 failed: '
                                  'DNS name for {0} host '
                                  'cannot be resolved.'.format(dns[0]))

        domain_name = output.split()[-1]
        cmd = "host {0}".format(domain_name)
        output = self.verify(100, self.retry_command, 3,
                             "'host' command failed. "
                             "DNS name cannot be resolved.",
                             "'host' command", 10, 5,
                             ssh_client.exec_command, cmd)
        LOG.debug(output)
        self.verify_response_true('has address {0}'.format(dns[0]) in output,
                                  'Step 4 failed: '
                                  'DNS name cannot be resolved.')
