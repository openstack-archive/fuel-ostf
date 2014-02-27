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

from fuel_health import savanna

LOG = logging.getLogger(__name__)


class PlatformSavannaTests(savanna.SavannaTest):
    """
    TestClass contains tests that check basic Savanna functionality.
    """

    @attr(type=['sanity', 'fuel'])
    def test_platform_savanna(self):
        """Savanna tests to create, list, start, checks and delete cluster
        Target component: Savanna

        Scenario:
            1. Savanna image with tags should be imported
            2. Send request to create node group template
            3. Send request to create cluster template
            4. Request the list of node group templates
            5. Request the list of cluster templates
            6. Send request to launch cluster
            7. Send request to delete cluster
            8. Send request to delete cluster template
            9. Send request to delete node group templates
        Duration:  100 m.

        Deployment tags: Savanna
        """
        fail_msg = ("Savanna image with tags wasn't imported into Glance, "
                    "please check "
                    "http://docs.mirantis.com/fuel/"
                    "fuel-4.1/user-guide.html#platform-tests-description")
        self.verify_response_true(
            self.verify(
                30,
                self._test_image,
                1, fail_msg,
                "Test images with tags"),
            "Step 1 failed: {msg}".format(msg=fail_msg))

        fail_msg = 'Fail create node group template.'
        self.verify(
            40,
            self._create_node_group_template_tt_dn_id,
            2, fail_msg,
            "Create node group templates",
            self.savanna_client)

        fail_msg = 'Fail create cluster template.'
        cluster_template = self.verify(
            40,
            self._create_tiny_cluster_template,
            3, fail_msg,
            "Create cluster templates",
            self.savanna_client)

        fail_msg = 'Fail list group templates.'
        self.verify(
            40,
            self._list_node_group_template,
            4, fail_msg,
            "List group templates",
            self.savanna_client)

        fail_msg = 'Fail list cluster templates.'
        self.verify(
            40,
            self._list_cluster_templates,
            5, fail_msg,
            "List cluster templates",
            self.savanna_client)

        fail_msg = 'Fail launch cluster.'
        self.verify(
            5400,
            self._create_cluster,
            6, fail_msg,
            "Launch cluster",
            self.savanna_client, cluster_template)

        fail_msg = 'Fail delete cluster.'
        self.verify(
            40,
            self._clean_clusters,
            7, fail_msg,
            "Delete cluster")

        fail_msg = 'Fail delete cluster template.'
        self.verify(
            40,
            self._clean_cluster_templates,
            8, fail_msg,
            "Delete cluster template")

        fail_msg = 'Fail delete node group  templates.'
        self.verify(
            40,
            self._clean_node_groups_templates,
            9, fail_msg,
            "Delete node group templates")
