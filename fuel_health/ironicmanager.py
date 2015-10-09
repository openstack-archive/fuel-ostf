# Copyright 2015 Mirantis, Inc.
# All Rights Reserved.
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
import traceback

from fuel_health.common.ssh import Client as SSHClient
from fuel_health import exceptions
import fuel_health.nmanager
import fuel_health.test

from ironicclient.common import utils

LOG = logging.getLogger(__name__)


class IronicTest(fuel_health.nmanager.NovaNetworkScenarioTest):
    """Manager that provides access to the Ironic python client for
    calling Ironic API.
    """

    @classmethod
    def setUpClass(cls):
        super(IronicTest, cls).setUpClass()
        if cls.manager.clients_initialized:
            cls.usr = cls.config.compute.controller_node_ssh_user
            cls.pwd = cls.config.compute.controller_node_ssh_password
            cls.key = cls.config.compute.path_to_private_key
            cls.timeout = cls.config.compute.ssh_timeout
            if not cls.ironic_client:
                LOG.warning('Ironic client was not initialized')

    def tearDown(self):
        super(IronicTest, self).tearDown()

    def node_create(self, **kwargs):
        """Create a new node."""
        node = self.ironic_client.node.create(**kwargs)
        self.addCleanup(self.node_delete, node)
        return node

    def node_delete(self, node):
        """Delete particular node."""
        try:
            self.ironic_client.node.delete(node.uuid)
        except Exception:
            LOG.debug(traceback.format_exc())

    def node_update(self, node, prop, value_prop):
        """Add property with value to node properties."""
        args = ['properties/%s=%s' % (prop, value_prop)]
        patch = utils.args_array_to_patch('add', args)
        return self.ironic_client.node.update(node.uuid, patch)

    def node_show(self, node, prop, value_prop):
        """Show detailed information about a node."""
        if node.instance_uuid:
            node = self.ironic_client.node.get_by_instance_uuid(
                node.instance_uuid)
        else:
            node = self.ironic_client.node.get(node.uuid)
        for p, v in node.properties.items():
            self.assertTrue(prop in p)
            self.assertTrue(value_prop in v)
        return node

    def _run_ssh_cmd_with_exit_code(self, host, cmd):
        """Open SSH session with host and execute command.
           Fail if exit code != 0
        """
        try:
            sshclient = SSHClient(host, self.usr, self.pwd,
                                  key_filename=self.key, timeout=self.timeout)
            return sshclient.exec_command(cmd)
        except Exception:
            LOG.debug(traceback.format_exc())
            self.fail("%s command failed." % cmd)

    def check_service_availability(self, nodes, cmd, expected,
                                   step, sleep, message):
        """Check running processes on nodes

           At least one controller should run ironic-api process.
           At least one Ironic node should run ironic-conductor process.
        """
        for node in nodes:
            output = self.verify(sleep, self._run_ssh_cmd_with_exit_code,
                                 1, "ironic-api service check failed.",
                                 "ironic-api service check",
                                 node, cmd)
            LOG.debug(output)
            try:
                self.assertTrue(expected in output)
                break
            except exceptions.SSHExecCommandFailed:
                LOG.info('Step %d failed: %s ' % (step, message))
                LOG.info("Will sleep for %d seconds and try again."
                         % sleep)
                LOG.debug(traceback.format_exc())
                return False
        return True

    def list_nodes(self):
        return self.ironic_client.node.list()

    def list_ports(self):
        return self.ironic_client.port.list()

    def list_drivers(self):
        return self.ironic_client.driver.list()

    def list_chassis(self):
        return self.ironic_client.chassis.list()