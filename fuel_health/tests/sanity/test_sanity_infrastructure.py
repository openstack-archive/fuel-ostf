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
            1. A controller's IP should be specified in
                controller_nodes parameter of the config file.
            2. The controller's domain name should be specified in
                controller_nodes_name parameter of the config file.
            3. SSH user credentials should be specified in
                controller_node_ssh_user/password parameters
                of the config file.
            4. List of services are expected to be run should be specified in
                enabled_services parameter of the config file.
    """
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        cls.host = cls.config.compute.controller_nodes
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
        if len(self.host):

            try:
                output = SSHClient(self.host[0],
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
            1. Connect to a controller node via SSH.
            2. Execute ping 8.8.8.8 from the controller.
            3. Check all the packages were received.
        Duration: 1-6 s.
        """
        if len(self.host):
            expected_output = "0% packet loss"
            cmd = "ping 8.8.8.8 -c 1"
            output = ''
            try:
                output = SSHClient(self.host[0],
                                   self.usr,
                                   self.pwd,
                                   key_filename=self.key,
                                   timeout=self.timeout).exec_command(cmd)
            except SSHExecCommandFailed as exc:
                output = "ping command failed."
                LOG.debug(exc)
                self.fail("Step 2 failed: " + output)
            except Exception as exc:
                LOG.debug(exc)
                self.fail("Step 1 failed: connection fail")
            LOG.debug(output)
            self.verify_response_true(expected_output in output,
                            'Step 3 failed: packets were lost')
        else:
            self.fail('Wrong tests configurations, controller '
                      'node ip is not specified')
