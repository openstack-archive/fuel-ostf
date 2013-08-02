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
from nose.plugins.attrib import attr

from fuel_health.common.ssh import Client as SSHClient
from fuel_health.exceptions import SSHExecCommandFailed
from fuel_health import nmanager

LOG = logging.getLogger(__name__)


class SanityInfrastructureTest(nmanager.SanityChecksTest):
    """TestClass contains tests check the whole OpenStack availability.
    Special requirements:
            1. A controller's IP should be specified.
            2. A compute's IP should be specified.
            3. SSH user credentials for the controller and the compute
                should be specified controller_node_ssh_user parameter
    """
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        cls.controllers = cls.config.compute.controller_nodes
        cls.computes = cls.config.compute.compute_nodes
        cls.usr = cls.config.compute.controller_node_ssh_user
        cls.pwd = cls.config.compute.controller_node_ssh_password
        cls.key = cls.config.compute.path_to_private_key
        cls.timeout = cls.config.compute.ssh_timeout

    @classmethod
    def tearDownClass(cls):
        pass

    @attr(type=['sanity', 'fuel'])
    def test_services_state(self):
        """Services execution monitoring
        Test all of the expected services are on.
        Target component: OpenStack

        Scenario:
            1. Execute nova-manage service list command on a controller node.
            2. Check there is no failed services (with XXX state).
        Duration: 2-8 s.
        """
        output = u'XXX'
        cmd = 'nova-manage service list'
        if not self.controllers:
            self.fail('Step 1 failed: there is no controller nodes')

        try:
            ssh_client = SSHClient(self.controllers[0],
                                   self.usr, self.pwd,
                                   key_filename=self.key,
                                   timeout=self.timeout)
            output = self.verify(50, ssh_client.exec_command,
                                 1, "'nova-manage' command"
                                    " execution failed. ",
                                 "nova-manage command execution",
                                 cmd)
        except SSHExecCommandFailed as exc:
            LOG.debug(exc)
            self.fail("Step 1 failed: %s commanf failed" % cmd)
        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 1 failed: unexpected error %s" % str(exc))

        LOG.debug(output)
        self.verify_response_true(
            u'XXX' not in output, 'Step 2 failed: Some nova services '
                                  'have not been started')

    @attr(type=['sanity', 'fuel'])
    def test_dns_state(self):
        """DNS availability
        Test dns is available.
        Target component: OpenStack

        Scenario:
            1. Execute ping 8.8.8.8 from a compute node.
            2. Check all the packets were received.
            3. Execute host 8.8.8.8 from the compute.
            4. Check 8.8.8.8 host is resolved.
        Duration: 1-12 s.
        """
        if not self.computes:
            self.fail('Step 1 failed: There are no compute nodes')

        cmd = "ping 8.8.8.8 -c 1 -w 1"
        try:
            ssh_client = SSHClient(self.computes[0],
                                   self.usr,
                                   self.pwd,
                                   key_filename=self.key,
                                   timeout=self.timeout)
            self.verify(50, ssh_client.exec_command, 1,
                        "'ping' command failed. ",
                        "'ping' command",
                        cmd)
        except SSHExecCommandFailed as exc:
            LOG.debug(exc)
            self.fail("Step 2 failed: ping to 8.8.8.8 was unsuccessful")
        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 1 failed: unexpected error %s" % str(exc))

        expected_output = "google"
        cmd = "host 8.8.8.8"

        try:
            output = self.verify(50, ssh_client.exec_command, 4,
                                 "'host' command failed. ",
                                 "'host' command",
                                 cmd)
        except SSHExecCommandFailed as exc:
            LOG.debug(exc)
            self.fail("Step 3 failed: %s command was unsuccessful" % cmd)

        self.verify_response_true(expected_output in output,
                                  'Step 4 failed: DNS name cannot be resolved')
