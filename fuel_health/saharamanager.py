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
import socket
import telnetlib
import time

from saharaclient.api import base as sab

from fuel_health import nmanager
from fuel_health.common.utils.data_utils import rand_name


LOG = logging.getLogger(__name__)


class SaharaTestsManager(nmanager.PlatformServicesBaseClass):

    def setUp(self):
        super(SaharaTestsManager, self).setUp()

        self.check_clients_state()

        # Timeout (in seconds) to wait for cluster deployment.
        self.cluster_timeout = 3000
        # Timeout (in seconds) to wait for cluster deletion.
        self.delete_timeout = 300
        # Timeout (in seconds) between status checks.
        self.request_timeout = 5
        # Timeout (in seconds) to wait for starting a Hadoop process
        # on a cluster node.
        self.process_timeout = 300
        # The minimum amount of available RAM for one of the compute nodes
        # to run Sahara platform tests.
        self.min_required_ram_mb = 4096
        # The path to the file where a SSH private key for Sahara tests
        # will be located.
        self.path_to_private_key = '/tmp/sahara-ostf.pem'

    def create_flavor(self, ram=1024, vcpus=1, disk=20):
        """This method creates a flavor for Sahara tests.

        All resources created by this method will be automatically deleted.
        """

        LOG.debug('Creating flavor for Sahara tests...')
        name = rand_name('sahara-flavor-')
        flavor = self.compute_client.flavors.create(name, ram, vcpus, disk)
        self.addCleanup(self.compute_client.flavors.delete, flavor.id)
        LOG.debug('Flavor for Sahara tests has been created.')

        return flavor.id

    def _create_key_pair(self):
        """This method creates a key pair for Sahara platform tests.

        All resources created by this method will be automatically deleted.
        """

        LOG.debug('Creating key pair for Sahara tests...')
        name = rand_name('sahara-key-pair-')
        key_pair = self.compute_client.keypairs.create(name)
        self.addCleanup(key_pair.delete)
        self._run_ssh_cmd('echo "{0}" > {1}'.format(key_pair.private_key,
                                                    self.path_to_private_key))
        LOG.debug('Key pair for Sahara tests has been created.')

        return name

    # Methods for finding and checking Sahara images.
    def find_and_check_image(self, tag_plugin, tag_version):
        """This method finds a correctly registered image for Sahara platform
        tests.

        It finds a Sahara image by specific tags and checks whether the image
        is correctly registered or not.
        """

        LOG.debug('Finding and checking image for Sahara...')
        image = self._find_image_by_tags(tag_plugin, tag_version)
        if (image is not None) and (
            '_sahara_username' in image.metadata) and (
                image.metadata['_sahara_username'] is not None):
            self.ssh_username = image.metadata['_sahara_username']
            LOG.debug('Image with name "{0}" is registered for Sahara with '
                      'username "{1}".'.format(image.name, self.ssh_username))
            return image.id
        LOG.debug('Image is not correctly registered or it is not '
                  'registered at all. Correct image for Sahara not found.')

    def _find_image_by_tags(self, tag_plugin, tag_version):
        """This method finds a Sahara image by specific tags."""

        tag_plug = '_sahara_tag_' + tag_plugin
        tag_ver = '_sahara_tag_' + tag_version
        for image in self.compute_client.images.list():
            if tag_plug in image.metadata and tag_ver in image.metadata:
                LOG.debug(
                    'Image with tags "{0}" and "{1}" found. Image name '
                    'is "{2}".'.format(tag_plugin, tag_version, image.name))
                return image
        LOG.debug('Image with tags "{0}" and "{1}" '
                  'not found.'.format(tag_plugin, tag_version))

    # Methods for creating Sahara resources.
    def create_cluster_template(self, name, plugin,
                                hadoop_version, node_groups, **kwargs):
        """This method creates a cluster template.

        It supports passing additional params using **kwargs and returns ID
        of created resource. All resources created by this method will be
        automatically deleted.
        """

        LOG.debug('Creating cluster template with name "{0}"...'.format(name))
        # TODO(ylobankov): remove this loop after fixing bug #1314578
        for node_group in node_groups:
            if 'floating_ip_pool' in node_group:
                if node_group['floating_ip_pool'] is None:
                    del node_group['floating_ip_pool']
        cl_template = self.sahara_client.cluster_templates.create(
            name, plugin, hadoop_version, node_groups=node_groups, **kwargs)
        self.addCleanup(self.delete_resource,
                        self.sahara_client.cluster_templates, cl_template.id)
        LOG.debug('Cluster template "{0}" has been created.'.format(name))

        return cl_template.id

    def create_cluster(self, name, plugin, hadoop_version,
                       default_image_id, node_groups=None, **kwargs):
        """This method creates a cluster.

        It supports passing additional params using **kwargs and returns ID
        of created resource. All resources created by this method will be
        automatically deleted.
        """

        key_pair_name = self._create_key_pair()
        LOG.debug('Creating cluster with name "{0}"...'.format(name))
        cluster = self.sahara_client.clusters.create(
            name, plugin, hadoop_version, default_image_id=default_image_id,
            user_keypair_id=key_pair_name, node_groups=node_groups, **kwargs)
        self.addCleanup(self.delete_resource,
                        self.sahara_client.clusters, cluster.id)
        LOG.debug('Cluster "{0}" has been created.'.format(name))

        return cluster.id

    # Methods for checking cluster deployment.
    def poll_cluster_status(self, cluster_id):
        """This method polls cluster status.

        It polls cluster every <request_timeout> seconds for some timeout and
        waits for when cluster gets to "Active" status.
        """

        LOG.debug('Waiting for cluster to build and get to "Active" status...')
        previous_cluster_status = 'An unknown cluster status'
        start = time.time()
        while time.time() - start < self.cluster_timeout:
            cluster = self.sahara_client.clusters.get(cluster_id)
            if cluster.status != previous_cluster_status:
                LOG.debug('Currently cluster is '
                          'in "{0}" status.'.format(cluster.status))
                previous_cluster_status = cluster.status
            if cluster.status == 'Active':
                return
            if cluster.status == 'Error':
                self.fail('Cluster failed to build and is in "Error" status.')
            time.sleep(self.request_timeout)

        self.fail('Cluster failed to get to "Active" '
                  'status within {0} seconds.'.format(self.cluster_timeout))

    def check_hadoop_services(self, cluster_id, processes_map):
        """This method checks deployment of Hadoop services on cluster.

        It checks whether all Hadoop processes are running on cluster nodes
        or not.
        """

        LOG.debug('Checking deployment of Hadoop services on cluster...')
        node_ips_and_processes = self._get_node_ips_and_processes(cluster_id)
        for node_ip, processes in node_ips_and_processes.items():
            LOG.debug('Checking Hadoop processes '
                      'on node {0}...'.format(node_ip))
            for process in processes:
                if process in processes_map:
                    LOG.debug('Checking process "{0}"...'.format(process))
                    for port in processes_map[process]:
                        self._check_port(node_ip, port)
                        LOG.debug('Process "{0}" is running and listening '
                                  'to port {1}.'.format(process, port))
            LOG.debug('All Hadoop processes are '
                      'running on node {0}.'.format(node_ip))
        LOG.debug(
            'All Hadoop services have been successfully deployed on cluster.')

    def _check_port(self, node_ip, port):
        """This method checks accessibility of specific port on cluster node.

        It tries to establish connection to the process on specific port every
        second for some timeout.
        """

        start = time.time()
        while time.time() - start < self.process_timeout:
            try:
                telnet_connection = telnetlib.Telnet(node_ip, port)
                if telnet_connection:
                    return telnet_connection.close()
            except socket.error:
                pass
            time.sleep(1)

        self.fail('Port {0} on node {1} is unreachable for '
                  '{2} seconds.'.format(port, node_ip, self.process_timeout))

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

        return node_ips_and_processes

    def check_ssh_connection(self, cluster_id):
        """This method checks capacity to establish a SSH connection
        to cluster nodes."""

        cmd = ('ssh -i {0} -l {1} -oUserKnownHostsFile=/dev/null '
               '-oStrictHostKeyChecking=no'.format(self.path_to_private_key,
                                                   self.ssh_username))
        for node_ip in self._get_node_ips_and_processes(cluster_id):
            self._run_ssh_cmd(cmd + ' {0} mkdir foo'.format(node_ip))

    # Methods for deleting resources.
    def delete_resource(self, resource_client, resource_id):
        """This method deletes the resource by its ID and checks whether
        the resource is really deleted or not."""

        LOG.debug('Deleting resource "{0}"...'.format(resource_id))
        if not self._make_request(resource_client.delete, resource_id):
            return
        self._wait_for_deletion(resource_client, resource_id)
        LOG.debug('Resource "{0}" has been deleted.'.format(resource_id))

    def _wait_for_deletion(self, resource_client, resource_id):
        """This method checks whether the resource is really deleted or not."""

        start = time.time()
        while time.time() - start < self.delete_timeout:
            if not self._make_request(resource_client.get, resource_id):
                return
            time.sleep(self.request_timeout)

        self.fail('Request timed out. '
                  'Timed out while waiting for one of the test resources '
                  'to delete within {0} seconds.'.format(self.delete_timeout))

    def _make_request(self, request, resource_id):
        """This method is a wrapper around an API request.

        The API request is wrapped in try/except block to correctly handle
        "404 Not Found" exception. If the resource exists, this method will
        return True. Otherwise it will return False.
        """

        try:
            request(resource_id)
        except sab.APIException as sahara_api_exc:
            if 'not found' in sahara_api_exc.message:
                LOG.debug('Resource "{0}" not found.'.format(resource_id))
                return False
            self.fail(sahara_api_exc.message)
        except Exception as exc:
            self.fail(exc.message)

        return True
