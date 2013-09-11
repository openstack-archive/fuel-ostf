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


class SanitySavannaTests(savanna.SavannaSanityChecksTest):
    """
    TestClass contains tests that check basic Savanna functionality.
    """

    @attr(type=['sanity', 'fuel'])
    def test_list_cluster_templates(self):
        """Test cluster template listing
        Target component: Savanna
        Scenario:
            1. Request the list of cluster templates.
        Duration: 20 s.
        """
        fail_msg = 'Cluster templates is unavailable'
        list_cluster_templates_resp = self.verify(20,
                                                  self._list_cluster_templates,
                                                  1, fail_msg,
                                                  "cluster template listing",
                                                  self.savanna_client)

    @attr(type=['sanity', 'fuel'])
    def test_01_create_node_group_template(self):
        """Test create/delete node group template
        Target component: Savanna
        Scenario:
            1. Create node group template tt dn
            2. Create node group template tt
            3. Create node group template dn
            4. Delete node group template tt dn
            5. Delete node group template tt
            6. Delete node group template dn
        Duration: 20 s.
        """
        fail_msg = 'Fail create node group template tt+dn'
        create_nodes_templates_tt_dn_resp = self.verify(
            20,
            self._create_node_group_template_tt_dn_id,
            1, fail_msg,
            "Create node group template",
            self.savanna_client)
        fail_msg = 'Fail create node group template tt'
        create_nodes_templates_tt_resp = self.verify(
            20,
            self._create_node_group_template_tt_id,
            2, fail_msg,
            "Create node group template",
            self.savanna_client)

        fail_msg = 'Fail create node group template dn'
        create_nodes_templates_dn_resp = self.verify(
            20,
            self._create_node_group_template_dn_id,
            3, fail_msg,
            "Create node group template",
            self.savanna_client)

        fail_msg = 'Fail delete node group template tt+dn'
        self.verify(
            20,
            self._delete_node_group_template,
            4, fail_msg,
            "Delete node group template",
            self.savanna_client, create_nodes_templates_tt_dn_resp)
        fail_msg = 'Fail delete node group template tt'
        self.verify(
            20,
            self._delete_node_group_template,
            5, fail_msg,
            "Delete node group template",
            self.savanna_client, create_nodes_templates_tt_resp)

        fail_msg = 'Fail delete node group template dn'
        self.verify(
            20,
            self._delete_node_group_template,
            6, fail_msg,
            "Delete node group template",
            self.savanna_client, create_nodes_templates_dn_resp)
