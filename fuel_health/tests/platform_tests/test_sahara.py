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

from fuel_health import saharamanager
from fuel_health.common.utils.data_utils import rand_name


LOG = logging.getLogger(__name__)


class SaharaClusterTest(saharamanager.SaharaTestsManager):
    _plugin_name = 'An unknown plugin name'
    _hadoop_version = 'An unknown Hadoop version'
    _worker_processes = 'An unknown list of worker processes'
    _master_processes = 'An unknown list of master processes'

    def setUp(self):
        super(SaharaClusterTest, self).setUp()

        doc_link = ('http://docs.mirantis.com/openstack/fuel/'
                    'fuel-{0}/user-guide.html#platform-tests-'
                    'description'.format(self.config.fuel.fuel_version))

        max_free_ram_mb, enough_ram = (
            self.check_compute_node_ram(self.min_required_ram_mb))
        if not enough_ram:
            ram_msg = ('This test requires more hardware resources of your '
                       'OpenStack cluster: at least one of the compute nodes '
                       'must have >= {0}MB of free RAM, but you have only '
                       '{1}MB on most appropriate compute node.'
                       .format(self.min_required_ram_mb, max_free_ram_mb))
            LOG.debug(ram_msg)
            self.skipTest(ram_msg)

        self.image_id = self.find_and_check_image(self._plugin_name,
                                                  self._hadoop_version)
        if not self.image_id:
            image_msg = ('Sahara image was not correctly registered or it was '
                         'not registered at all. Please refer to the Mirantis '
                         'OpenStack documentation ({0}) to find out how to '
                         'register image for Sahara.'.format(doc_link))
            LOG.debug(image_msg)
            self.skipTest(image_msg)

        flavor_id = self.create_flavor()
        self.cl_template = {
            'name': rand_name('sahara-cluster-template-'),
            'plugin': self._plugin_name,
            'hadoop_version': self._hadoop_version,
            'node_groups': [
                {
                    'name': 'master',
                    'flavor_id': flavor_id,
                    'node_processes': self._master_processes,
                    'floating_ip_pool': self.neutron_external_network_id,
                    'auto_security_group': True,
                    'count': 1
                },
                {
                    'name': 'worker',
                    'flavor_id': flavor_id,
                    'node_processes': self._worker_processes,
                    'floating_ip_pool': self.neutron_external_network_id,
                    'auto_security_group': True,
                    'count': 1
                }
            ],
            'net_id': self.neutron_private_network_id,
            'cluster_configs': {'HDFS': {'dfs.replication': 1}},
            'description': 'Test cluster template'
        }
        self.cluster = {
            'name': rand_name('sahara-cluster-'),
            'plugin': self._plugin_name,
            'hadoop_version': self._hadoop_version,
            'default_image_id': self.image_id,
            'description': 'Test cluster'
        }


class VanillaTwoClusterTest(SaharaClusterTest):
    _plugin_name = 'vanilla'
    _hadoop_version = '2.4.1'
    _worker_processes = ['nodemanager', 'datanode']
    _master_processes = ['resourcemanager', 'namenode',
                         'oozie', 'historyserver', 'secondarynamenode']

    def setUp(self):
        super(VanillaTwoClusterTest, self).setUp()

        self.processes_map = {
            'resourcemanager': [8032, 8088],
            'namenode': [9000, 50070],
            'nodemanager': [8042],
            'datanode': [50010, 50020, 50075],
            'secondarynamenode': [50090],
            'oozie': [11000],
            'historyserver': [19888]
        }

    def test_vanilla_two_cluster(self):
        """Sahara test for launching a simple Vanilla2 cluster
        Target component: Sahara

        Scenario:
            1. Create a cluster template
            2. Create a cluster
            3. Wait for the cluster to build and get to "Active" status
            4. Check deployment of Hadoop services on the cluster
            5. Check capacity to log into cluster nodes via SSH
            6. Delete the cluster
            7. Delete the cluster template

        Duration:  3600 s.
        Deployment tags: Sahara
        """

        fail_msg = 'Failed to create cluster template.'
        msg = 'creating cluster template'
        cl_template_id = self.verify(30, self.create_cluster_template,
                                     1, fail_msg, msg, **self.cl_template)

        self.cluster['cluster_template_id'] = cl_template_id
        fail_msg = 'Failed to create cluster.'
        msg = 'creating cluster'
        cluster_id = self.verify(30, self.create_cluster, 2,
                                 fail_msg, msg, **self.cluster)

        fail_msg = 'Failed to poll cluster status.'
        msg = 'polling cluster status'
        self.verify(self.cluster_timeout,
                    self.poll_cluster_status, 3, fail_msg, msg, cluster_id)

        fail_msg = 'Failed to check deployment of Hadoop services on cluster.'
        msg = 'checking deployment of Hadoop services on cluster'
        self.verify(self.process_timeout, self.check_hadoop_services,
                    4, fail_msg, msg, cluster_id, self.processes_map)

        fail_msg = 'Failed to log into cluster nodes via SSH.'
        msg = 'logging into cluster nodes via SSH'
        self.verify(
            30, self.check_node_access_via_ssh, 5, fail_msg, msg, cluster_id)

        fail_msg = 'Failed to delete cluster.'
        msg = 'deleting cluster'
        self.verify(self.delete_timeout, self.delete_resource, 6,
                    fail_msg, msg, self.sahara_client.clusters, cluster_id)

        fail_msg = 'Failed to delete cluster template.'
        msg = 'deleting cluster template'
        self.verify(30, self.delete_resource, 7, fail_msg, msg,
                    self.sahara_client.cluster_templates, cl_template_id)
