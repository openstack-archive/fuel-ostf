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

from fuel_health.common.utils.data_utils import rand_name
from fuel_health import saharamanager


class SaharaTemplatesTest(saharamanager.SaharaTestsManager):
    _plugin_name = 'An unknown plugin name'
    _hadoop_version = 'An unknown Hadoop version'
    _node_processes = 'An unknown list of processes'

    def setUp(self):
        super(SaharaTemplatesTest, self).setUp()

        flavor_id = self.create_flavor()
        self.ng_template = {
            'name': rand_name('sahara-ng-template-'),
            'plugin_name': self._plugin_name,
            'hadoop_version': self._hadoop_version,
            'flavor_id': flavor_id,
            'node_processes': self._node_processes,
            'description': 'Test node group template'
        }
        self.cl_template = {
            'name': rand_name('sahara-cl-template-'),
            'plugin_name': self._plugin_name,
            'hadoop_version': self._hadoop_version,
            'node_groups': [
                {
                    'name': 'all-in-one',
                    'flavor_id': flavor_id,
                    'node_processes': self._node_processes,
                    'count': 1
                }
            ],
            'description': 'Test cluster template'
        }
        self.client = self.sahara_client


class VanillaTwoTemplatesTest(SaharaTemplatesTest):
    def setUp(self):
        mapping_versions_of_plugin = {
            "6.1": "2.4.1",
            "7.0": "2.6.0",
            "8.0": "2.7.1",
            "9.0": "2.7.1",
            "9.1": "2.7.1"
        }
        self._plugin_name = 'vanilla'
        self._hadoop_version = mapping_versions_of_plugin.get(
            self.config.fuel.fuel_version)
        self._node_processes = ['resourcemanager', 'namenode',
                                'secondarynamenode', 'oozie', 'historyserver',
                                'nodemanager', 'datanode']
        super(VanillaTwoTemplatesTest, self).setUp()

    def test_vanilla_two_templates(self):
        """Sahara test for checking CRUD operations on Vanilla2 templates
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

        Duration: 80 s.
        Available since release: 2014.2-6.1
        Deployment tags: Sahara
        """

        fail_msg = 'Failed to create node group template.'
        ng_template = self.verify(10, self.client.node_group_templates.create,
                                  1, fail_msg, 'creating node group template',
                                  **self.ng_template)

        fail_msg = 'Failed to get node group template.'
        self.verify(10, self.client.node_group_templates.get, 2,
                    fail_msg, 'getting node group template', ng_template.id)

        fail_msg = 'Failed to list node group templates.'
        self.verify(10, self.client.node_group_templates.list, 3,
                    fail_msg, 'listing node group templates')

        fail_msg = 'Failed to delete node group template.'
        self.verify(10, self.client.node_group_templates.delete, 4,
                    fail_msg, 'deleting node group template', ng_template.id)

        fail_msg = 'Failed to create cluster template.'
        cl_template = self.verify(10, self.client.cluster_templates.create, 5,
                                  fail_msg, 'creating cluster template',
                                  **self.cl_template)

        fail_msg = 'Failed to get cluster template.'
        self.verify(10, self.sahara_client.cluster_templates.get, 6,
                    fail_msg, 'getting cluster template', cl_template.id)

        fail_msg = 'Failed to list cluster templates.'
        self.verify(10, self.sahara_client.cluster_templates.list, 7,
                    fail_msg, 'listing cluster templates')

        fail_msg = 'Failed to delete cluster template.'
        self.verify(10, self.sahara_client.cluster_templates.delete, 8,
                    fail_msg, 'deleting cluster template', cl_template.id)


class HDPTwoTemplatesTest(SaharaTemplatesTest):
    _plugin_name = 'ambari'
    _hadoop_version = '2.3'
    _node_processes = ["Ambari", "YARN Timeline Server", "DataNode",
                       "MapReduce History Server", "NameNode", "NodeManager",
                       "Oozie", "ResourceManager", "SecondaryNameNode",
                       "ZooKeeper"]

    def test_hdp_two_templates(self):
        """Sahara test for checking CRUD operations on HDP2 templates
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

        Duration: 80 s.
        Available since release: 2015.1.0-8.0
        Deployment tags: Sahara
        """

        fail_msg = 'Failed to create node group template.'
        ng_template = self.verify(10, self.client.node_group_templates.create,
                                  1, fail_msg, 'creating node group template',
                                  **self.ng_template)

        fail_msg = 'Failed to get node group template.'
        self.verify(10, self.client.node_group_templates.get, 2,
                    fail_msg, 'getting node group template', ng_template.id)

        fail_msg = 'Failed to list node group templates.'
        self.verify(10, self.client.node_group_templates.list, 3,
                    fail_msg, 'listing node group templates')

        fail_msg = 'Failed to delete node group template.'
        self.verify(10, self.client.node_group_templates.delete, 4,
                    fail_msg, 'deleting node group template', ng_template.id)

        fail_msg = 'Failed to create cluster template.'
        cl_template = self.verify(10, self.client.cluster_templates.create, 5,
                                  fail_msg, 'creating cluster template',
                                  **self.cl_template)

        fail_msg = 'Failed to get cluster template.'
        self.verify(10, self.sahara_client.cluster_templates.get, 6,
                    fail_msg, 'getting cluster template', cl_template.id)

        fail_msg = 'Failed to list cluster templates.'
        self.verify(10, self.sahara_client.cluster_templates.list, 7,
                    fail_msg, 'listing cluster templates')

        fail_msg = 'Failed to delete cluster template.'
        self.verify(10, self.sahara_client.cluster_templates.delete, 8,
                    fail_msg, 'deleting cluster template', cl_template.id)
