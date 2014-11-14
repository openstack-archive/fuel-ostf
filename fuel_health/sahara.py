# Copyright 2013 Mirantis, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging
import socket
import telnetlib
import time

from saharaclient.api import base as sab

from fuel_health import nmanager
from fuel_health.common.utils.data_utils import rand_name


LOG = logging.getLogger(__name__)


class SaharaManager(nmanager.PlatformServicesBaseClass):
    """Base class for Sahara sanity tests and platform tests."""

    def setUp(self):
        super(SaharaManager, self).setUp()

        self.check_clients_state()

        # Timeout (in seconds) to wait for cluster deployment.
        self.cluster_timeout = 3600
        # Timeout (in seconds) to wait for cluster deletion.
        self.delete_timeout = 300
        # Timeout (in seconds) between status checks.
        self.request_timeout = 5
        # Timeout (in seconds) to wait for starting a Hadoop process
        # on a cluster node.
        self.process_timeout = 300
        # Minimal required RAM of one of the compute nodes to run Sahara
        # platform tests.
        self.min_required_ram = 4096

        self.public_net = 'net04_ext'  # Name of Neutron public network
        self.private_net = 'net04'     # Name of Neutron private network

        self.node_group_templates = []
        self.cluster_templates = []
        self.clusters = []
        self.flavors = []

    # Method for creating a flavor for Sahara tests.
    def create_flavor(self, ram=2048, vcpus=1, disk=20):
        """This method creates a flavor for Sahara tests.

        All resources created by this method will be automatically deleted.
        """

        LOG.debug('Creating flavor for Sahara tests...')
        name = rand_name('sahara-ostf-flavor-')
        flavor = self.compute_client.flavors.create(name, ram, vcpus, disk)
        self.flavors.append(flavor.id)
        LOG.debug('Flavor for Sahara tests has been created.')

        return flavor.id

    # Methods for finding and checking Sahara images.
    def find_and_check_image(self, tag_plugin_name, tag_hadoop_version):
        """This method finds a correct image for Sahara platform tests.

        It finds a Sahara image by specific tags and checks whether the image
        is properly registered or not.
        """

        LOG.debug('Finding and checking image for Sahara...')
        image = self._find_image_by_tags(tag_plugin_name, tag_hadoop_version)
        if (image is not None) and (
            '_sahara_username' in image.metadata) and (
                image.metadata['_sahara_username'] is not None):
            LOG.debug('Image with name "%s" is registered for Sahara with '
                      'username "%s".' % (image.name,
                                          image.metadata['_sahara_username']))
            return image.id
        LOG.debug('Image is not properly registered or it is not '
                  'registered at all. Correct image for Sahara not found.')

    def _find_image_by_tags(self, tag_plugin_name, tag_hadoop_version):
        """This method finds a Sahara image by specific tags."""

        tag_plugin = '_sahara_tag_%s' % tag_plugin_name
        tag_version = '_sahara_tag_%s' % tag_hadoop_version
        for image in self.compute_client.images.list():
            if tag_plugin in image.metadata and tag_version in image.metadata:
                LOG.debug(
                    'Image with tags "%s" and "%s" found. Image name is "%s".'
                    % (tag_plugin_name, tag_hadoop_version, image.name))
                return image
        LOG.debug('Image with tags "%s" and "%s" '
                  'not found.' % (tag_plugin_name, tag_hadoop_version))

    # Method for retrieving network info of OpenStack cloud.
    def retrieve_network_info(self):
        """This method retrieves network info of OpenStack cloud.

        If Neutron is used as network manager, it returns IDs of public and
        private networks accordingly. If Nova is used as network manager and
        auto assignment of floating IPs is enabled, it returns None. Otherwise,
        it returns the name of a floating IP pool and None.
        """

        cmd_nova = ('grep auto_assign_floating_ip '
                    '/etc/nova/nova.conf | grep True')
        cmd_neutron = ('grep -E '
                       '"network_api_class=nova.network.neutronv2.api.API" '
                       '/etc/nova/nova.conf')
        output_nova, output_nova_err = self._run_ssh_cmd(cmd_nova)
        output_neutron, output_neutron_err = self._run_ssh_cmd(cmd_neutron)

        if output_neutron or str(output_neutron_err).find(
                'network_api_class=nova.network.neutronv2.api.API') > 0:
            LOG.debug('OpenStack network manager is Neutron.')
            LOG.debug('Neutron public network is "%s".' % self.public_net)
            LOG.debug('Neutron private network is "%s".' % self.private_net)
            public_net_id = self.compute_client.networks.find(
                label=self.public_net).id
            private_net_id = self.compute_client.networks.find(
                label=self.private_net).id

            return public_net_id, private_net_id

        if output_nova or str(output_nova_err).find('True') > 0:
            LOG.debug('OpenStack network manager is Nova. '
                      'Auto assignment of floating IPs is enabled.')

            return None, None

        else:
            LOG.debug('OpenStack network manager is Nova. '
                      'Auto assignment of floating IPs is not enabled.')
            floating_ip_pool = (
                self.compute_client.floating_ip_pools.list()[0].name)
            LOG.debug('Floating IP pool is "%s".' % floating_ip_pool)

            return floating_ip_pool, None

    # Methods for creating Sahara resources.
    def create_cluster_template(self, name, plugin_name, hadoop_version,
                                node_groups, **kwargs):
        """This method creates a cluster template.

        It supports passing additional params using **kwargs and returns ID
        of created resource. All resources created by this method will be
        automatically deleted.
        """

        LOG.debug('Creating cluster template with name "%s"...' % name)
        # TODO(ylobankov): remove this loop after fixing bug #1314578
        for node_group in node_groups:
            if 'floating_ip_pool' in node_group:
                if node_group['floating_ip_pool'] is None:
                    del node_group['floating_ip_pool']

        cluster_template = self.sahara_client.cluster_templates.create(
            name, plugin_name, hadoop_version, node_groups=node_groups,
            **kwargs)
        self.cluster_templates.append(cluster_template.id)
        LOG.debug('Cluster template "%s" has been created.' % name)

        return cluster_template.id

    def create_cluster(self, name, plugin_name, hadoop_version,
                       default_image_id, node_groups=None, **kwargs):
        """This method creates a cluster.

        It supports passing additional params using **kwargs and returns ID
        of created resource. All resources created by this method will be
        automatically deleted.
        """

        LOG.debug('Creating cluster with name "%s"...' % name)
        cluster = self.sahara_client.clusters.create(
            name, plugin_name, hadoop_version,
            default_image_id=default_image_id,
            node_groups=node_groups, **kwargs)
        self.clusters.append(cluster.id)
        LOG.debug('Cluster "%s" has been created.' % name)

        return cluster.id

    # Methods for checking cluster deployment.
    def poll_cluster_status(self, cluster_id):
        """This method polls cluster status.

        It polls cluster every <request_timeout> seconds for some time and
        waits for when cluster gets to "Active" status.
        """

        LOG.debug('Waiting for cluster to build and get to "Active" status...')
        previous_cluster_status = 'An unknown cluster status'
        start = time.time()
        while time.time() - start < self.cluster_timeout:
            cluster = self.sahara_client.clusters.get(cluster_id)
            if cluster.status != previous_cluster_status:
                LOG.debug(
                    'Currently cluster is in "%s" status.' % cluster.status)
                previous_cluster_status = cluster.status
            if cluster.status == 'Active':
                return
            if cluster.status == 'Error':
                self.fail('Cluster failed to build and is in "Error" status.')
            time.sleep(self.request_timeout)

        self.fail('Cluster failed to get to "Active" '
                  'status within %d seconds.' % self.cluster_timeout)

    def check_hadoop_services(self, cluster_id, processes_map):
        """This method checks Hadoop services on cluster.

        It checks whether all Hadoop processes are running on cluster nodes
        or not.
        """

        LOG.debug('Checking Hadoop services on cluster...')
        node_ips_and_processes = self._get_node_ips_and_processes(cluster_id)
        for node_ip, processes in node_ips_and_processes.items():
            LOG.debug('Checking Hadoop processes on node %s...' % node_ip)
            for process in processes:
                if process in processes_map:
                    LOG.debug('Checking process "%s"...' % process)
                    for port in processes_map[process]:
                        self._check_port(node_ip, port)
                        LOG.debug('Process "%s" is running and '
                                  'listening to port %d.' % (process, port))
            LOG.debug('All Hadoop processes are running on node %s.' % node_ip)
        LOG.debug('All Hadoop services are running on cluster.')

    def _check_port(self, node_ip, port):
        """This method checks accessibility of specific port on cluster node.

        It tries to establish connection to the process on specific port every
        second for some time.
        """

        start = time.time()
        while time.time() - start < self.process_timeout:
            try:
                telnet_connection = telnetlib.Telnet(node_ip, port)
                if telnet_connection:
                    telnet_connection.close()
                    return
            except socket.error:
                pass
            time.sleep(1)

        self.fail('Port %d on node %s is unreachable '
                  'for %d seconds.' % (port, node_ip, self.process_timeout))

    # Methods for retrieving information of cluster.
    def _get_node_ips_and_processes(self, cluster_id):
        """This method makes dictionary with information of cluster nodes.

        Each key of dictionary is IP of cluster node, value is list of Hadoop
        processes that must be started on node.
        """

        data = self.sahara_client.clusters.get(cluster_id)
        node_ips_and_processes = {}
        for node_group in data.node_groups:
            for instance in node_group['instances']:
                node_ip = instance['management_ip']
                node_ips_and_processes[node_ip] = node_group['node_processes']

        # For example:
        #   node_ips_and_processes = {
        #       '172.18.168.181': ['tasktracker'],
        #       '172.18.168.94': ['secondarynamenode', 'oozie'],
        #       '172.18.168.208': ['jobtracker', 'namenode'],
        #       '172.18.168.93': ['tasktracker', 'datanode'],
        #       '172.18.168.44': ['tasktracker', 'datanode'],
        #       '172.18.168.233': ['datanode']
        #   }

        return node_ips_and_processes

    # Methods for deleting resources.
    def delete_resources(self, resources,
                         resource_client, resource_is_cluster=False):
        for resource in resources[:]:
            try:
                resource_client.delete(resource)
            except Exception as e:
                self.fail('Failed while deleting '
                          'one of the test resources. ' + str(e))
            if resource_is_cluster:
                self._delete_timeout(resource_client, resource)
            resources.remove(resource)

    def _delete_timeout(self, resource_client, resource):
        """This method checks whether resource is really deleted or not."""

        timeout = self.delete_timeout
        start = time.time()
        while time.time() - start < timeout:
            try:
                resource_client.get(resource)
            except sab.APIException as sahara_api_exception:
                if 'not found' in sahara_api_exception.message:
                    return
                self.fail(sahara_api_exception.message)
            except Exception as e:
                self.fail(e.message)

            time.sleep(self.request_timeout)

        self.fail('Request timed out. Timed out while waiting for one of '
                  'the test resources to delete within %d seconds.' % timeout)

    def tearDown(self):
        self.delete_resources(self.clusters, self.sahara_client.clusters,
                              resource_is_cluster=True)
        self.delete_resources(self.cluster_templates,
                              self.sahara_client.cluster_templates)
        self.delete_resources(self.node_group_templates,
                              self.sahara_client.node_group_templates)
        self.delete_resources(self.flavors, self.compute_client.flavors)

        super(SaharaManager, self).tearDown()
