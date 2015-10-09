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

import fuel_health.common.ssh
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
