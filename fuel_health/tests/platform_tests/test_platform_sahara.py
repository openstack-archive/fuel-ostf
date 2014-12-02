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

from fuel_health import sahara

LOG = logging.getLogger(__name__)


class PlatformSaharaTests(sahara.SaharaTest):
    """
    TestClass contains tests that check basic Sahara functionality.
    """
    def setUp(self):
        super(PlatformSaharaTests, self).setUp()

        doc_link = ('http://docs.mirantis.com/openstack/fuel/'
                    'fuel-6.0/user-guide.html#platform-tests-description')

        ram_msg = ('This test requires more resources: at least one of the '
                   'compute nodes must have >= {0} MB of free RAM, but you '
                   'have only {1} MB on most appropriate compute node.'
                   .format(self.min_required_ram, self.max_available_ram))
        if not self.enough_ram:
            LOG.debug(ram_msg)
            self.skipTest(ram_msg)

        image_msg = ('Sahara image was not properly registered or '
                     'was not registered at all. Please refer to the '
                     'Mirantis OpenStack documentation ({0}) to find out '
                     'how to register image for Sahara.'.format(doc_link))
        if not self.check_image():
            LOG.debug(image_msg)
            self.skipTest(image_msg)

    def test_platform_sahara(self):
        """Sahara test for launching a simple cluster
        Target component: Sahara

        Scenario:
            1. Send request to create node group template
            2. Send request to create cluster template
            3. Send request to launch cluster
            4. Send request to delete cluster
            5. Send request to delete cluster template
            6. Send request to delete node group template
        Duration:  100 m.

        Deployment tags: Sahara
        """

        fail_msg = 'Failed to create node group template.'
        self.verify(40, self.create_node_group_template_tt_dn,
                    1, fail_msg, 'Create node group template')

        fail_msg = 'Failed to create cluster template.'
        cluster_template = self.verify(40, self.create_tiny_cluster_template,
                                       2, fail_msg, 'Create cluster template')

        fail_msg = 'Failed to launch cluster.'
        self.verify(5400, self.create_sahara_cluster,
                    3, fail_msg, 'Launch cluster', cluster_template.id)

        fail_msg = 'Failed to delete cluster.'
        self.verify(40, self._clean_clusters, 4, fail_msg, 'Delete cluster')

        fail_msg = 'Failed to delete cluster template.'
        self.verify(40, self._clean_cluster_templates,
                    5, fail_msg, 'Delete cluster template')

        fail_msg = 'Failed to delete node group template.'
        self.verify(40, self._clean_node_groups_templates,
                    6, fail_msg, 'Delete node group template')
