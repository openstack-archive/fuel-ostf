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

from fuel_health.common.ssh import Client as SSHClient
from fuel_health import nmanager
from time import sleep

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
        cls.controllers = cls.config.compute.controller_nodes
        cls.computes = cls.config.compute.compute_nodes
        cls.usr = cls.config.compute.controller_node_ssh_user
        cls.pwd = cls.config.compute.controller_node_ssh_password
        cls.key = cls.config.compute.path_to_private_key
        cls.timeout = cls.config.compute.ssh_timeout

    @classmethod
    def tearDownClass(cls):
        pass

    def test_001_services_state(self):
        """Check that required services are running
        Target component: OpenStack

        Scenario:
            1. Execute nova-manage service list command on a controller node.
            2. Check there are no failed services (with XXX state).
        Duration: 50 s.
        """
        output = u'XXX'
        cmd = 'nova-manage service list'
        if not self.controllers:
            self.fail('Step 1 failed: there are no controller nodes.')
        ssh_client = SSHClient(self.controllers[0],
                               self.usr, self.pwd,
                               key_filename=self.key,
                               timeout=self.timeout)
        output = self.verify(50, ssh_client.exec_command,
                             1, "'nova-manage' command execution failed. ",
                             "nova-manage command execution",
                             cmd)
        LOG.debug(output)
        try:
            self.verify_response_true(
                u'XXX' not in output, 'Step 2 failed: Some nova services '
                'have not been started.')
        except:
            LOG.info("Will sleep for 60 seconds and try again")
            sleep(60)
            self.verify_response_true(
                u'XXX' not in output, 'Step 2 failed: Some nova services '
                'have not been started.')

    def test_002_internet_connectivity_from_compute(self):
        """Check internet connectivity from a compute
        Target component: OpenStack

        Scenario:
            1. Execute ping 8.8.8.8 command from a compute node.
        Duration: 40 s.
        """
        if not self.computes:
            self.fail('Step 1 failed: There are no compute nodes')

        cmd = "ping 8.8.8.8 -c 1 -w 1"
        ssh_client = SSHClient(self.computes[0],
                               self.usr,
                               self.pwd,
                               key_filename=self.key,
                               timeout=self.timeout)
        self.verify(50, ssh_client.exec_command, 1,
                    "'ping' command failed. Looks like there is no "
                    "Internet connection on the compute node.",
                    "'ping' command",
                    cmd)

    def test_003_dns_resolution(self):
        """Check DNS resolution on compute node
        Target component: OpenStack

        Scenario:
            1. Execute host 8.8.8.8 command from a compute node.
            2. Check 8.8.8.8 host was successfully resolved
            3. Check host google.com command from the compute node.
            4. Check google.com host was successfully resolved.
        Duration: 60 s.
        """
        if not self.computes:
            self.fail('Step 1 failed: There are no compute nodes')
        ssh_client = SSHClient(self.computes[0],
                               self.usr,
                               self.pwd,
                               key_filename=self.key,
                               timeout=self.timeout)
        expected_output = "google"
        cmd = "host 8.8.8.8"
        output = self.verify(50, ssh_client.exec_command, 1,
                             "'host' command failed. Looks like there is no "
                             "Internet connection on the compute node.",
                             "'ping' command",
                             cmd)
        LOG.debug(output)
        self.verify_response_true(expected_output in output,
                                  'Step 2 failed: '
                                  'DNS name for 8.8.8.8 host '
                                  'cannot be resolved.')

        expected_output = "google.com has address"
        cmd = "host google.com"
        output = self.verify(50, ssh_client.exec_command, 3,
                             "'host' command failed. "
                             "DNS name cannot be resolved.",
                             "'host' command",
                             cmd)
        LOG.debug(output)
        self.verify_response_true(expected_output in output,
                                  'Step 4 failed: '
                                  'DNS name cannot be resolved.')
