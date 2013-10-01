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


class SanitySavannaTests(savanna.SavannaTest):
    """
    TestClass contains tests that check basic Savanna functionality.
    """

    @attr(type=['sanity', 'fuel'])
    def test_platform_savanna(self):
        """Test create/list/start/delete Savanna cluster
        Target component: Savanna
        Scenario:
            1. Create node group template
            2. Create cluster template
            3. List node group templates
            4. List cluster templates
            5. Create cluster
            6. Delete cluster
            7. Delete cluster template
            8. Delete node group templates
        Duration:  20 m.
        """
        fail_msg = 'Fail create node group tasktracker and datanode template.'
        create_nodes_templates_tt_dn_resp = self.verify(
            20,
            self._create_node_group_template_tt_dn_id,
            1, fail_msg,
            "Create node group tasktracker and datanode template",
            self.savanna_client)

        fail_msg = 'Fail create cluster template.'
        cluster_template = self.verify(
            20,
            self._create_tiny_cluster_template,
            2, fail_msg,
            "Create cluster templates",
            self.savanna_client)

        fail_msg = 'Fail list group template.'
        self.verify(
            20,
            self._list_node_group_template,
            3, fail_msg,
            "List group templates",
            self.savanna_client)

        fail_msg = 'Fail list cluster template.'
        self.verify(
            20,
            self._list_cluster_templates,
            4, fail_msg,
            "List cluster templates",
            self.savanna_client)

        fail_msg = 'Fail create cluster.'
        self.verify(
            1200,
            self._create_cluster,
            5, fail_msg,
            "Create cluster",
            self.savanna_client, cluster_template)

        fail_msg = 'Fail delete cluster.'
        self.verify(
            20,
            self._clean_clusters,
            6, fail_msg,
            "Delete cluster")

        fail_msg = 'Fail delete cluster template.'
        self.verify(
            20,
            self._clean_cluster_templates,
            7, fail_msg,
            "Delete cluster template")

        fail_msg = 'Fail delete node group  template.'
        self.verify(
            20,
            self._clean_node_groups_templates,
            8, fail_msg,
            "Delete node group template")
