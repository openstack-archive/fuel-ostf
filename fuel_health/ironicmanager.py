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
        cls.nodes = []
        if cls.manager.clients_initialized:
            if not cls.ironic_client:
                LOG.warning('Ironic client was not initialized')

    def tearDown(self):
        LOG.debug("Deleting nodes created by Ironic test")
        self._clean_nodes()
        super(IronicTest, self).tearDown()

    def _list_nodes(self, client):
        return client.node.list()

    def node_create(self, client, **kwargs):
        node = client.node.create(**kwargs)
        self.nodes.append(node.uuid)
        return node

    def node_delete(self, client, node):
        client.node.delete(node.uuid)
        return self.nodes.remove(node.uuid)

    def _clean_nodes(self):
        pass

    def node_update(self, client, node, prop, value_prop):
        args = ['properties/%s=%s' % (prop, value_prop)]
        patch = utils.args_array_to_patch('add', args)
        return client.node.update(node.uuid, patch)


