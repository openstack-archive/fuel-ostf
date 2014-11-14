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

from fuel_health import sahara
from fuel_health.common.utils.data_utils import rand_name


class TemplatesTest(sahara.SaharaManager):
    """Test class contains checks for basic Sahara functionality."""

    def setUp(self):
        super(TemplatesTest, self).setUp()

        plugin_name = 'vanilla'
        hadoop_version = '2.4.1'
        node_processes = ['resourcemanager', 'namenode', 'secondarynamenode',
                          'oozie', 'historyserver', 'nodemanager', 'datanode']

        self.client = self.sahara_client
        self.ng_template = {
            'name': rand_name('sahara-ng-template-'),
            'plugin_name': plugin_name,
            'hadoop_version': hadoop_version,
            'flavor_id': self.flavor_id,
            'node_processes': node_processes,
            'description': 'Test node group template'
        }
        self.cl_template = {
            'name': rand_name('sahara-cl-template-'),
            'plugin_name': plugin_name,
            'hadoop_version': hadoop_version,
            'node_groups': [
                {
                    'name': 'all-in-one',
                    'flavor_id': self.flavor_id,
                    'node_processes': node_processes,
                    'count': 1
                }
            ],
            'description': 'Test cluster template'
        }

    def test_vanilla_templates(self):
        """Create/get/list/delete node group template and cluster template
        Target component: Sahara

        Scenario:
            1. Create a simple node group template
            2. Get the node group template
            3. List node group templates
            4. Delete the node group template
            5. Create a simple cluster template
            6. Get the cluster template
            7. List cluster templates
            8. Delete the cluster template

        Duration: 20 s.
        Deployment tags: Sahara
        """

        fail_msg = 'Failed to create node group template.'
        msg = 'Create simple node group template'
        ng_template = self.verify(30, self.client.node_group_templates.create,
                                  1, fail_msg, msg, **self.ng_template)

        fail_msg = 'Failed to get node group template.'
        self.verify(30, self.client.node_group_templates.get, 2,
                    fail_msg, 'Get node group template', ng_template.id)

        fail_msg = 'Failed to list node group templates.'
        self.verify(30, self.client.node_group_templates.list, 3,
                    fail_msg, 'List node group templates')

        fail_msg = 'Failed to delete node group template.'
        self.verify(30, self.client.node_group_templates.delete, 4,
                    fail_msg, 'Delete node group template', ng_template.id)

        fail_msg = 'Failed to create cluster template.'
        msg = 'Create simple cluster template'
        cl_template = self.verify(30, self.client.cluster_templates.create, 5,
                                  fail_msg, msg, **self.cl_template)

        fail_msg = 'Failed to get cluster template.'
        self.verify(30, self.sahara_client.cluster_templates.get, 6,
                    fail_msg, 'Get cluster template', cl_template.id)

        fail_msg = 'Failed to list cluster templates.'
        self.verify(30, self.sahara_client.cluster_templates.list, 7,
                    fail_msg, 'List cluster templates')

        fail_msg = 'Failed to delete cluster template.'
        self.verify(30, self.sahara_client.cluster_templates.delete, 8,
                    fail_msg, 'Delete cluster template', cl_template.id)
