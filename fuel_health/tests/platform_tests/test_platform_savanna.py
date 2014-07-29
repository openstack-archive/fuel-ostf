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

from fuel_health import savanna

LOG = logging.getLogger(__name__)


class PlatformSavannaTests(savanna.SavannaTest):
    """
    TestClass contains tests that check basic Savanna functionality.
    """
    def setUp(self):
        super(PlatformSavannaTests, self).setUp()
        msg = ("Sahara image with tags wasn't imported into Glance, "
               "please check "
               "http://docs.mirantis.com/openstack/fuel/fuel-5.0/"
               "user-guide.html#platform-tests-description")

        if not self._test_image():
            LOG.debug(msg)
            self.skipTest(msg)

    def test_platform_savanna(self):
        """Sahara tests to create, list, start, checks and delete cluster
        Target component: Sahara

        Scenario:
            1. Send request to create node group template
            2. Send request to create cluster template
            3. Request the list of node group templates
            4. Request the list of cluster templates
            5. Send request to launch cluster
            6. Send request to delete cluster
            7. Send request to delete cluster template
            8. Send request to delete node group templates
        Duration:  100 m.

        Deployment tags: Sahara
        """

        fail_msg = 'Fail create node group template.'
        self.verify(40, self.create_node_group_template_tt_dn, 1, fail_msg,
                    "Create node group templates")

        fail_msg = 'Fail create cluster template.'
        cluster_template = self.verify(40, self.create_tiny_cluster_template,
                                       2, fail_msg, "Create cluster templates")

        fail_msg = 'Fail list group templates.'
        self.verify(40, self._list_node_group_template, 3, fail_msg,
                    "List group templates")

        fail_msg = 'Fail list cluster templates.'
        self.verify(40, self._list_cluster_templates, 4, fail_msg,
                    "List cluster templates")

        fail_msg = 'Fail launch cluster.'
        self.verify(5400, self.create_sahara_cluster, 5, fail_msg,
                    "Launch cluster", cluster_template.id)

        fail_msg = 'Fail delete cluster.'
        self.verify(40, self._clean_clusters, 6, fail_msg,
                    "Delete cluster")

        fail_msg = 'Fail delete cluster template.'
        self.verify(40, self._clean_cluster_templates, 7, fail_msg,
                    "Delete cluster template")

        fail_msg = 'Fail delete node group  templates.'
        self.verify(40, self._clean_node_groups_templates, 8, fail_msg,
                    "Delete node group templates")
