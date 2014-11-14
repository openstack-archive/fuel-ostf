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
from fuel_health.common.utils.data_utils import rand_name


LOG = logging.getLogger(__name__)


class SaharaClusterTest(sahara.SaharaManager):
    _plugin_name = 'An unknown plugin name'
    _hadoop_version = 'An unknown hadoop version'

    def setUp(self):
        super(SaharaClusterTest, self).setUp()

        doc_link = ('http://docs.mirantis.com/openstack/fuel/'
                    'fuel-6.0/user-guide.html#platform-tests-description')

        max_available_ram, enough_ram = (
            self.check_compute_node_ram(self.min_required_ram))
        if not enough_ram:
            ram_msg = ('This test requires more resources: at least one of '
                       'the compute nodes must have >= {0}MB of free RAM, but '
                       'you have only {1}MB on most appropriate compute node.'
                       .format(self.min_required_ram, max_available_ram))
            LOG.debug(ram_msg)
            self.skipTest(ram_msg)

        self.image_id = self.find_and_check_image(self._plugin_name,
                                                  self._hadoop_version)
        if not self.image_id:
            image_msg = ('Sahara image was not properly registered or was not '
                         'registered at all. Please refer to the Mirantis '
                         'OpenStack documentation ({0}) to find out how to '
                         'register image for Sahara.'.format(doc_link))
            LOG.debug(image_msg)
            self.skipTest(image_msg)


class VanillaClusterTest(SaharaClusterTest):
    """Test class contains checks for basic Sahara functionality."""

    _plugin_name = 'vanilla'
    _hadoop_version = '2.4.1'

    def setUp(self):
        super(VanillaClusterTest, self).setUp()

        master_processes = ['resourcemanager', 'namenode',
                            'oozie', 'historyserver', 'secondarynamenode']
        worker_processes = ['nodemanager', 'datanode']
        self.processes_map = {
            'resourcemanager': [8032, 8088],
            'namenode': [9000, 50070],
            'nodemanager': [8042],
            'datanode': [50010, 50020, 50075],
            'secondarynamenode': [50090],
            'oozie': [11000],
            'historyserver': [19888]
        }
        flavor_id = self.create_flavor(ram=1024, vcpus=1, disk=20)

        floating_ip_pool, net_id = self.retrieve_network_info()
        self.cl_template = {
            'name': rand_name('sahara-cluster-template-'),
            'plugin_name': self._plugin_name,
            'hadoop_version': self._hadoop_version,
            'node_groups': [
                {
                    'name': 'master',
                    'flavor_id': flavor_id,
                    'node_processes': master_processes,
                    'floating_ip_pool': floating_ip_pool,
                    'auto_security_group': True,
                    'count': 1
                },
                {
                    'name': 'worker',
                    'flavor_id': flavor_id,
                    'node_processes': worker_processes,
                    'floating_ip_pool': floating_ip_pool,
                    'auto_security_group': True,
                    'count': 1
                }
            ],
            'net_id': net_id,
            'cluster_configs': {'HDFS': {'dfs.replication': 1}},
            'description': 'Test cluster template'
        }
        self.cluster = {
            'name': rand_name('sahara-cluster-'),
            'plugin_name': self._plugin_name,
            'hadoop_version': self._hadoop_version,
            'default_image_id': self.image_id,
            'description': 'Test cluster'
        }

    def test_vanilla_cluster(self):
        """Sahara test for launching a simple Vanilla cluster
        Target component: Sahara

        Scenario:
            1. Create a cluster template
            2. Create a cluster
            3. Waiting for the cluster to build and get to "Active" status
            4. Checking Hadoop services on the cluster
            5. Delete the cluster
            6. Delete the cluster template

        Duration:  3600 s.
        Deployment tags: Sahara
        """

        fail_msg = 'Failed to create cluster template.'
        msg = 'Create cluster template'
        cl_template_id = self.verify(30, self.create_cluster_template, 1,
                                     fail_msg, msg, **self.cl_template)

        self.cluster['cluster_template_id'] = cl_template_id
        fail_msg = 'Failed to create cluster.'
        cluster_id = self.verify(30, self.create_cluster, 2,
                                 fail_msg, 'Create cluster', **self.cluster)

        fail_msg = 'Failed to poll cluster status.'
        self.verify(self.cluster_timeout, self.poll_cluster_status, 3,
                    fail_msg, 'Poll cluster status', cluster_id)

        fail_msg = 'Failed to check Hadoop services on cluster.'
        self.verify(self.process_timeout, self.check_hadoop_services, 4,
                    fail_msg, 'Poll cluster status', self.processes_map)

        fail_msg = 'Failed to delete cluster.'
        self.verify(self.delete_timeout, self.delete_resources, 5,
                    fail_msg, 'Delete cluster', self.clusters,
                    self.sahara_client.clusters, resource_is_cluster=True)

        fail_msg = 'Failed to delete cluster template.'
        self.verify(30, self.delete_resources, 6, fail_msg,
                    'Delete cluster template', self.cluster_templates,
                    self.sahara_client.cluster_templates)
