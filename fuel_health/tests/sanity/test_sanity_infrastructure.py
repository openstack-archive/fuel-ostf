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
from nose.tools import timed

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
    @timed(50)
    def test_services_state(self):
        """Services execution monitoring
        Test all of the expected services are on.
        Target component: OpenStack

        Scenario:
            1. Connect to a controller node via SSH.
            2. Execute nova-manage service list command.
            3. Check there is no failed services (with XXX state)
        Duration: 2-8 s.
        """
        output_msg = ''
        cmd = 'nova-manage service list'
        if len(self.controllers):

            try:
                output = SSHClient(self.controllers[0],
                                   self.usr, self.pwd,
                                   key_filename=self.key,
                                   timeout=self.timeout).exec_command(cmd)
            except SSHExecCommandFailed as exc:
                output_msg = "Error: 'nova-manage' command execution failed."
                LOG.debug(exc)
                self.fail("Step 2 failed: " + output_msg)
            except Exception as exc:
                LOG.debug(exc)
                self.fail("Step 1 failed: connection fail")

            output_msg = output_msg or (
                'Some nova services has not been started')
            LOG.debug(output)
            self.verify_response_true(
                u'XXX' not in output, 'Step 3 failed: ' + output_msg)
        else:
            self.fail('Wrong tests configurations, controller '
                      'node ip is not specified')

    @attr(type=['sanity', 'fuel'])
    @timed(50)
    def test_dns_state(self):
        """DNS availability
        Test dns is available.
        Target component: OpenStack

        Scenario:
            1. Connect to a compute node via SSH.
            2. Execute ping 8.8.8.8 from the compute.
            3. Check all the packages were received.
            4. Execute host 8.8.8.8 from the controller.
            5. Check 8.8.8.8 host is resolved.
        Duration: 1-12 s.
        """
        if len(self.computes):
            expected_output = "0% packet loss"
            cmd = "ping 8.8.8.8 -c 1 -w 1"
            output = ''
            try:
                output = SSHClient(self.computes[0],
                                   self.usr,
                                   self.pwd,
                                   key_filename=self.key,
                                   timeout=self.timeout).exec_command(cmd)
            except SSHExecCommandFailed as exc:
                LOG.debug(exc)
                if ("exit status: 1" not in exc._error_string):
                    self.fail("Step 2 failed: ping command failed. "
                              "Details: " + exc._error_string)
            except Exception as exc:
                LOG.debug(exc)
                self.fail("Step 1 failed: connection fail")
            LOG.debug(output)
            self.verify_response_true(expected_output in output,
                            'Step 3 failed: packets to 8.8.8.8 were lost, '
                            'there is no Internet connection'
                            ' on the compute node')

            expected_output = ("8.8.8.8.in-addr.arpa domain name pointer "
                               "google-public-dns-a.google.com.")
            cmd = "host 8.8.8.8"
            output = ''
            try:
                output = SSHClient(self.computes[0],
                                   self.usr,
                                   self.pwd,
                                   key_filename=self.key,
                                   timeout=self.timeout).exec_command(cmd)
            except SSHExecCommandFailed as exc:
                LOG.debug(exc)
                if("Host 8.8.8.8.in-addr.arpa. not found" not in
                       exc._error_string):
                    self.fail("Step 4 failed: host command failed. "
                              "Details: " + exc._error_string)
            except Exception as exc:
                LOG.debug(exc)
                self.fail("Step 4 failed: connection to the compute fail")
            LOG.debug(output)
            self.verify_response_true(expected_output in output,
                            'Step 5 failed: DNS name cannot be resolved')
        else:
            self.fail('Wrong tests configurations, compute '
                      'node ip is not specified')
