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

from fuel_health import nmanager
import fuel_health.test

from fuel_health.common.ssh import Client as SSHClient
from ironicclient.common import utils
from ironicclient import exc as ironic_exc

LOG = logging.getLogger(__name__)


class IronicTest(nmanager.SanityChecksTest):
    """Provide access to the python-ironicclient for calling Ironic API."""

    @classmethod
    def setUpClass(cls):
        """Setup Ironic client and credentials."""
        super(IronicTest, cls).setUpClass()
        if cls.manager.clients_initialized:
            cls.usr = cls.config.compute.controller_node_ssh_user
            cls.pwd = cls.config.compute.controller_node_ssh_password
            cls.key = cls.config.compute.path_to_private_key
            cls.timeout = cls.config.compute.ssh_timeout
            if not cls.ironic_client:
                LOG.warning('Ironic client was not initialized')

    def node_create(self, **kwargs):
        """Create a new node."""
        node = self.ironic_client.node.create(**kwargs)
        self.addCleanup(self.node_delete, node)
        return node

    def node_delete(self, node):
        """Delete particular node."""
        try:
            self.ironic_client.node.delete(node.uuid)
        except ironic_exc.NotFound:
            LOG.debug(traceback.format_exc())

    def node_update(self, node, prop, value_prop, row='properties'):
        """Add property with value to node properties."""
        args = ['{0}/{1}={2}'.format(row, prop, value_prop)]
        patch = utils.args_array_to_patch('add', args)
        return self.ironic_client.node.update(node.uuid, patch)

    def node_show(self, node):
        """Show detailed information about a node."""
        if node.instance_uuid:
            n = self.ironic_client.node.get_by_instance_uuid(
                node.instance_uuid)
        else:
            n = self.ironic_client.node.get(node.uuid)
        return n

    def check_service_availability(self, nodes, cmd, expected, timeout=30):
        """Check running processes on nodes.

        Check that output from specified command contain expected part
        at least on one node.
        """
        def check_services():
            for node in nodes:
                remote = SSHClient(node, self.usr, self.pwd,
                                   key_filename=self.key,
                                   timeout=self.timeout)
                try:
                    output = remote.exec_command(cmd)
                    LOG.debug(output)
                    if expected in output:
                        return True
                except Exception:
                    pass
            return False

        if not fuel_health.test.call_until_true(check_services, 30, timeout):
            self.fail('Failed to discover service {0} '
                      'within specified timeout'.format(expected))
        return True

    def list_nodes(self):
        """Get list of nodes."""
        return self.ironic_client.node.list()

    def list_ports(self):
        """Get list of ports."""
        return self.ironic_client.port.list()

    def list_drivers(self):
        """Get list of drivers."""
        return self.ironic_client.driver.list()

    def list_chassis(self):
        """Get list of chassis."""
        return self.ironic_client.chassis.list()
