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
    def test_01_create_node_group_template(self):
        """Test create/list/delete Savanna node group and cluster templates
        Target component: Savanna
        Scenario:
            1. Create node group tasktracker and datanode template
            2. Create node group tasktracker template
            3. Create node group datanode template
            4. Create cluster template
            5. List node group templates
            6. List cluster templates
            7. Delete cluster template
            8. Delete node templates
            9. Delete cluster flavors
        Duration: 20 s.
        """
        fail_msg = 'Fail create node group tasktracker and datanode template'
        create_nodes_templates_tt_dn_resp = self.verify(
            20,
            self._create_node_group_template_tt_dn_id,
            1, fail_msg,
            "Create node group tasktracker and datanode template",
            self.savanna_client)

        fail_msg = 'Fail create node group tasktracker template'
        create_nodes_templates_tt_resp = self.verify(
            20,
            self._create_node_group_template_tt_id,
            2, fail_msg,
            "Create node group tasktracker template",
            self.savanna_client)

        fail_msg = 'Fail create node group datanode template'
        create_nodes_templates_dn_resp = self.verify(
            20,
            self._create_node_group_template_dn_id,
            3, fail_msg,
            "Create node group datanode template",
            self.savanna_client)

        fail_msg = 'Fail create cluster template'
        cluster_template = self.verify(
            20,
            self._create_cluster_template,
            4, fail_msg,
            "Create cluster templates",
            self.savanna_client)

        fail_msg = 'Fail list group template'
        self.verify(
            20,
            self._list_node_group_template,
            5, fail_msg,
            "List group templates",
            self.savanna_client)

        fail_msg = 'Fail list cluster template'
        self.verify(
            20,
            self._list_cluster_templates,
            6, fail_msg,
            "List cluster templates",
            self.savanna_client)

        fail_msg = 'Fail delete cluster template'
        self.verify(
            20,
            self._clean_cluster_templates,
            7, fail_msg,
            "Delete cluster templates")

        fail_msg = 'Fail delete datanodes template'
        self.verify(
            20,
            self._clean_node_groups_templates,
            8, fail_msg,
            "Delete datanodes template")

        fail_msg = 'Fail delete clusters flavors'
        self.verify(
            20,
            self._clean_flavors,
            9, fail_msg,
            "Delete clusters flavors")
