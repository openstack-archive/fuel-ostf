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


class SanitySavannaTests(savanna.SavannaTest):
    """
    TestClass contains tests that check basic Savanna functionality.
    """

    def test_sanity_savanna(self):
        """Sahara tests to create/list/delete node group and cluster templates
        Target component: Sahara

        Scenario:
            1. Create node group task tracker and data node template
            2. Send request to create node group task tracker template
            3. Send request to create node group data node template
            4. Send request to create cluster template
            5. Request the list of node group templates
            6. Request the list of cluster templates
            7. Send request to delete cluster template
            8. Send request to delete node templates
            9. Send request to delete sahara flavor

        Duration: 100 s.
        Deployment tags: Sahara
        """
        fail_msg = 'Fail create node group tasktracker and datanode templates.'
        self.verify(40, self.create_node_group_template_tt_dn, 1, fail_msg,
                    "Create node group tasktracker and datanode templates")

        fail_msg = 'Fail create node group tasktracker template.'
        self.verify(40, self.create_node_group_template_tt, 2, fail_msg,
                    "Create node group tasktracker template")

        fail_msg = 'Fail create node group datanode template.'
        self.verify(40, self.create_node_group_template_dn, 3, fail_msg,
                    "Create node group datanode template")

        fail_msg = 'Fail create cluster template.'
        self.verify(40, self.create_cluster_template, 4, fail_msg,
                    "Create cluster template")

        fail_msg = 'Fail list group templates.'
        self.verify(40, self._list_node_group_template, 5, fail_msg,
                    "List group templates")

        fail_msg = 'Fail list cluster templates.'
        self.verify(40, self._list_cluster_templates, 6, fail_msg,
                    "List cluster templates")

        fail_msg = 'Fail delete cluster template.'
        self.verify(40, self._clean_cluster_templates, 7, fail_msg,
                    "Delete cluster templates")

        fail_msg = 'Fail delete datanodes templates.'
        self.verify(40, self._clean_node_groups_templates, 8, fail_msg,
                    "Delete datanodes templates")

        fail_msg = 'Fail delete clusters flavors.'
        self.verify(40, self._clean_flavors, 9, fail_msg,
                    "Delete clusters flavors")
