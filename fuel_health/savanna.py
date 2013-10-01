# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
import time

from fuel_health.common.ssh import Client as SSHClient
from fuel_health.exceptions import SSHExecCommandFailed

import fuel_health.nmanager as nmanager


LOG = logging.getLogger(__name__)

try:
    import savannaclient.api.client
except:
    LOG.warning('Savanna client could not be imported.')

class SavannaClientManager(nmanager.OfficialClientManager):
    """
    Manager that provides access to the Savanna python client for
    calling Savanna API.
    """

    def __init__(self):
        """
        This method allows to initialize authentication before
        each test case and define parameters of
        Savanna API Service
        """
        super(SavannaClientManager, self).__init__()
        self.savanna_client = self._get_savanna_client()
        self.client_attr_names.append('savanna_client')

    def _get_savanna_client(self, username=None, password=None):
        auth_url = self.config.identity.uri
        tenant_name = self.config.identity.admin_tenant_name
        savanna_ip = self.config.compute.controller_nodes[0]
        savanna_url = 'http://%s:8386/v1.0' % savanna_ip
        LOG.debug(savanna_url)
        if not username:
            username = self.config.identity.admin_username
        if not password:
            password = self.config.identity.admin_password
        return savannaclient.api.client.Client(username=username,
                                               api_key=password,
                                               project_name=tenant_name,
                                               auth_url=auth_url,
                                               savanna_url=savanna_url)


class SavannaOfficialClientTest(nmanager.OfficialClientTest):
    manager_class = SavannaClientManager


class SavannaTest(SavannaOfficialClientTest):
    """
    Base class for openstack sanity tests for Savanna
    """
    @classmethod
    def setUpClass(cls):
        super(SavannaTest, cls).setUpClass()
        cls.flavors = []
        cls.node_groups = []
        cls.cluster_templates = []
        cls.clusters = []
        cls.keys = []
        cls.plugin = 'vanilla'
        cls.plugin_version = '1.1.2'
        cls.TT_CONFIG = {'Task Tracker Heap Size': 515}
        cls.DN_CONFIG = {'Data Node Heap Size': 513}
        cls.CLUSTER_HDFS_CONFIG = {'dfs.replication': 2}
        cls.CLUSTER_MR_CONFIG = {
            'mapred.map.tasks.speculative.execution': False,
            'mapred.child.java.opts': '-Xmx100m'}
        cls.CLUSTER_GENERAL_CONFIG = {'Enable Swift': True}
        cls.SNN_CONFIG = {'Name Node Heap Size': 510}
        cls.NN_CONFIG = {'Name Node Heap Size': 512}
        cls.JT_CONFIG = {'Job Tracker Heap Size': 514}
        cls.V_HADOOP_USER = 'hadoop'
        cls.V_NODE_USERNAME = 'ubuntu'
        cls.HDP_HADOOP_USER = 'hdfs'
        cls.HDP_NODE_USERNAME = 'cloud-user'
        cls.CLUSTER_CREATION_TIMEOUT = '20'
        cls.USER_KEYPAIR_ID = 'ostf-savanna'
        cls.PLUGIN_NAME = 'vanilla'
        cls.HADOOP_VERSION = '1.1.2'
        cls.IMAGE_NAME = 'savanna'
        cls.CLUSTER_NAME = 'ostf-savanna-cluster'
        cls.JT_PORT = 50030
        cls.NN_PORT = 50070
        cls.TT_PORT = 50060
        cls.DN_PORT = 50075
        cls.SEC_NN_PORT = 50090

    def _create_node_group_template_and_get_id(
            self, client, name, plugin_name, hadoop_version, description,
            volumes_per_node, volume_size, node_processes, node_configs):
        if not self.flavors:
            flavor = self.compute_client.flavors.create('SavannaFlavor',
                                                        512, 1, 700)
            self.flavors.append(flavor.id)
        data = client.node_group_templates.create(
            name, plugin_name, hadoop_version, self.flavors[0], description,
            volumes_per_node, volume_size, node_processes, node_configs
        )
        node_group_template_id = str(data.id)
        return node_group_template_id

    @classmethod
    def _create_cluster_template_and_get_id(
            cls, client, name, plugin_name, hadoop_version, description,
            cluster_configs, node_groups,  anti_affinity):

        data = client.cluster_templates.create(
            name, plugin_name, hadoop_version, description, cluster_configs,
            node_groups, anti_affinity
        )
        cluster_template_id = data.id
        return cluster_template_id

    def _check_cluster_state(self, client, cluster_state, cluster_id):
        if cluster_state == 'Error':
            client.clusters.delete(cluster_id)
            client.fail('Cluster state == \'Error\'')
        if cluster_state != 'Active':
            client.clusters.delete(cluster_id)
            client.fail(
                'Cluster state != \'Active\', passed %d minutes'
                % self.CLUSTER_CREATION_TIMEOUT)

    def _get_cluster_state(self, client, cluster_id):
        data = client.clusters.get(cluster_id)
        i = 1
        while str(data.status) != 'Active':
            LOG.debug('CLUSTER STATUS:' + str(i * 10) + ' sec:' + str(data.status))
            print('CLUSTER STATUS:' + str(i * 10) + ' sec:' + str(data.status))
            if str(data.status) == 'Error':
                LOG.debug('\n' + str(i * 10) + ' sec:' + str(data) + '\n')
                return 'Error'
            if i > self.CLUSTER_CREATION_TIMEOUT * 6:
                LOG.debug('\n' + str(i * 10) + ' sec:' + str(data) + '\n')
                return str(data.status)
            data = client.clusters.get(cluster_id)
            time.sleep(10)
            i += 1
        return str(data.status)

    @classmethod
    def _get_cluster_node_ip_list_with_node_processes(
            cls, client, cluster_id):
        data = client.clusters.get(cluster_id)
        node_groups = data.node_groups
        node_ip_list_with_node_processes = {}
        for node_group in node_groups:
            instances = node_group['instances']
            for instance in instances:
                node_ip = instance['management_ip']
                node_ip_list_with_node_processes[node_ip] = node_group[
                    'node_processes']
        LOG.debug('node_ip_list_with_node_processes:\n%s' % node_ip_list_with_node_processes)
        return node_ip_list_with_node_processes

    def _create_cluster_and_get_info(
            self, client, plugin_name, hadoop_version, cluster_template_id,
            image_name, description, cluster_configs, node_groups,
            anti_affinity):
        self.keys.append(
            self.compute_client.keypairs.create(self.USER_KEYPAIR_ID))
        image_id = str(self.compute_client.images.find(name=image_name).id)
        data = client.clusters.create(
            self.CLUSTER_NAME, plugin_name, hadoop_version,
            cluster_template_id, image_id, description, cluster_configs,
            node_groups, self.USER_KEYPAIR_ID, anti_affinity
        )
        cluster_id = data.id
        self.clusters.append(cluster_id)
        cluster_state = self._get_cluster_state(client, cluster_id)
        self._check_cluster_state(client, cluster_state, cluster_id)
        node_ip_list_with_node_processes = \
            self._get_cluster_node_ip_list_with_node_processes(client, cluster_id)
        node_info = self._get_node_info(
            node_ip_list_with_node_processes, plugin_name
        )
        self._await_active_workers_for_namenode(node_info, plugin_name)
        return {
            'cluster_id': cluster_id,
            'node_ip_list': node_ip_list_with_node_processes,
            'node_info': node_info
        }

    def _get_node_info(self, node_ip_list_with_node_processes, plugin_name):
        tasktracker_count = 0
        datanode_count = 0
        node_count = 0
        port_map = {
            'jobtracker': self.JT_PORT,
            'namenode': self.NN_PORT,
            'tasktracker': self.TT_PORT,
            'datanode': self.DN_PORT,
            'secondary_namenode': self.SEC_NN_PORT
        }
        self.tt = 'tasktracker'
        self.dn = 'datanode'
        self.nn = 'namenode'
        if plugin_name == 'hdp':
            port_map = {
                'JOBTRACKER': self.JT_PORT,
                'NAMENODE': self.NN_PORT,
                'TASKTRACKER': self.TT_PORT,
                'DATANODE': self.DN_PORT,
                'SECONDARY_NAMENODE': self.SEC_NN_PORT
            }
            self.tt = 'TASKTRACKER'
            self.dn = 'DATANODE'
            self.nn = 'NAMENODE'
        for node_ip, processes in node_ip_list_with_node_processes.items():
            node_count += 1
            if self.tt in processes:
                tasktracker_count += 1
            if self.dn in processes:
                datanode_count += 1
            if self.nn in processes:
                namenode_ip = node_ip
        return {
            'namenode_ip': namenode_ip,
            'tasktracker_count': tasktracker_count,
            'datanode_count': datanode_count,
            'node_count': node_count
        }

    @classmethod
    def _get_cluster_node_ip_list_with_node_processes(
            cls, client, cluster_id):
        data = client.clusters.get(cluster_id)
        node_groups = data.node_groups
        node_ip_list_with_node_processes = {}
        for node_group in node_groups:
            instances = node_group['instances']
            for instance in instances:
                node_ip = instance['management_ip']
                node_ip_list_with_node_processes[node_ip] = node_group[
                    'node_processes']
        LOG.debug(node_ip_list_with_node_processes)
        return node_ip_list_with_node_processes


    def _create_cluster(self, client, cluster_template_id):
        self._create_cluster_and_get_info(
            client,
            self.PLUGIN_NAME,
            self.HADOOP_VERSION,
            cluster_template_id,
            self.IMAGE_NAME,
            description='test cluster',
            cluster_configs={},
            node_groups=None,
            anti_affinity=[])


    def _create_node_group_template_tt_dn_id(self, client):
        node_group_template_tt_dn_id = \
            self._create_node_group_template_and_get_id(
                client,
                'ostf-savanna-tt-dn',
                self.plugin,
                self.plugin_version,
                description='test node group template',
                volumes_per_node=0,
                volume_size=1,
                node_processes=['tasktracker', 'datanode'],
                node_configs={
                    'HDFS': self.DN_CONFIG,
                    'MapReduce': self.TT_CONFIG
                }
            )
        self.node_groups.append(node_group_template_tt_dn_id)
        return node_group_template_tt_dn_id

    def _create_node_group_template_tt_id(self, client):
        node_group_template_tt_id = \
            self._create_node_group_template_and_get_id(
                client,
                'ostf-savanna-tt',
                self.plugin,
                self.plugin_version,
                description='test node group template',
                volumes_per_node=0,
                volume_size=0,
                node_processes=['tasktracker'],
                node_configs={
                    'MapReduce': self.TT_CONFIG
                }
            )
        self.node_groups.append(node_group_template_tt_id)
        return node_group_template_tt_id

    def _create_node_group_template_dn_id(self, client):
        node_group_template_tt_id = \
            self._create_node_group_template_and_get_id(
                client,
                'ostf-savanna-dd',
                self.plugin,
                self.plugin_version,
                description='test node group template',
                volumes_per_node=0,
                volume_size=0,
                node_processes=['datanode'],
                node_configs={
                    'MapReduce': self.TT_CONFIG
                }
            )
        self.node_groups.append(node_group_template_tt_id)
        return node_group_template_tt_id

    def _create_cluster_template(self, client):
        cluster_template_id = self._create_cluster_template_and_get_id(
            client,
            'ostf-savanna-test-cluster-template',
            self.plugin,
            self.plugin_version,
            description='test cluster template',
            cluster_configs={
                'HDFS': self.CLUSTER_HDFS_CONFIG,
                'MapReduce': self.CLUSTER_MR_CONFIG,
                'general': self.CLUSTER_GENERAL_CONFIG
            },
            node_groups=[
                dict(
                    name='master-node-jt-nn',
                    flavor_id=self.flavors[0],
                    node_processes=['namenode', 'jobtracker'],
                    node_configs={
                        'HDFS': self.NN_CONFIG,
                        'MapReduce': self.JT_CONFIG
                    },
                    count=1),
                dict(
                    name='master-node-sec-nn',
                    flavor_id=self.flavors[0],
                    node_processes=['secondarynamenode'],
                    node_configs={
                        'HDFS': self.SNN_CONFIG
                    },
                    count=1),
                dict(
                    name='worker-node-tt-dn',
                    node_group_template_id=self.node_groups[0],
                    count=2),
                dict(
                    name='worker-node-dn',
                    node_group_template_id=self.node_groups[1],
                    count=1),
                dict(
                    name='worker-node-tt',
                    node_group_template_id=self.node_groups[2],
                    count=1)
            ],
            anti_affinity=[]
        )
        self.cluster_templates.append(cluster_template_id)
        return cluster_template_id

    def _create_tiny_cluster_template(self, client):
        cluster_template_id = self._create_cluster_template_and_get_id(
            client,
            'ostf-savanna-test-cluster-template',
            self.plugin,
            self.plugin_version,
            description='test cluster template',
            cluster_configs={
                'HDFS': self.CLUSTER_HDFS_CONFIG,
                'MapReduce': self.CLUSTER_MR_CONFIG,
                'general': self.CLUSTER_GENERAL_CONFIG
            },
            node_groups=[
                dict(
                    name='master-node-jt-nn',
                    flavor_id=self.flavors[0],
                    node_processes=['namenode', 'jobtracker'],
                    node_configs={
                        'HDFS': self.NN_CONFIG,
                        'MapReduce': self.JT_CONFIG
                    },
                    count=1),
                dict(
                    name='worker-node-tt-dn',
                    node_group_template_id=self.node_groups[0],
                    count=1),
            ],
            anti_affinity=[]
        )
        self.cluster_templates.append(cluster_template_id)
        return cluster_template_id

    def _await_active_workers_for_namenode(self, node_info, plugin_name):
        attempt_count = 100
        if plugin_name == 'vanilla':
            hadoop_user = self.V_HADOOP_USER
            node_username = self.V_NODE_USERNAME
        elif plugin_name == 'hdp':
            hadoop_user = self.HDP_HADOOP_USER
        LOG.debug('Starting ssh execute')
        try:
            SSHClient(host=self.config.compute.controller_nodes[0],
                      username=self.config.compute.controller_node_ssh_user,
                      pkey=self.config.compute.path_to_private_key,
                      timeout=300
                      ).exec_command('echo "%s" > /tmp/ostf-savanna.pem' %
                             self.keys[0].private_key)
            SSHClient(host=self.config.compute.controller_nodes[0],
                      username=self.config.compute.controller_node_ssh_user,
                      pkey=self.config.compute.path_to_private_key,
                      timeout=300
                      ).exec_command('chmod 600  /tmp/ostf-savanna.pem')
        except SSHExecCommandFailed as exc:
            output_msg = "Command failed."
            LOG.debug(exc)
            self.fail(output_msg)
        while True:
            try:
                cmd = ('ssh -i /tmp/ostf-savanna.pem -l %s '
                       '-oUserKnownHostsFile=/dev/null '
                       '-oStrictHostKeyChecking=no %s '
                       'sudo -u %s -i "hadoop job '
                       '-list-active-trackers"' %
                       (self.V_NODE_USERNAME, node_info['namenode_ip'], hadoop_user))

                active_tasktracker_count = SSHClient(
                    host=self.config.compute.controller_nodes[0],
                    username=self.config.compute.controller_node_ssh_user,
                    pkey=self.config.compute.path_to_private_key,
                    timeout=300
                    ).exec_command(cmd)
                LOG.debug('active_tasktracker_count:%s' % active_tasktracker_count)
                print('active_tasktracker_count:%s' % active_tasktracker_count)
            except SSHExecCommandFailed as exc:
                output_msg = "Command failed."
                LOG.debug(exc)
                self.fail(output_msg)
            try:
                cmd = ('ssh -i /tmp/ostf-savanna.pem -l %s '
                       '-oUserKnownHostsFile=/dev/null '
                       '-oStrictHostKeyChecking=no %s '
                       'sudo -u %s -i "hadoop dfsadmin -report" '
                       '| grep "Datanodes available:.*" | awk '
                       '\'{print $3}\'' %
                       (self.V_NODE_USERNAME, node_info['namenode_ip'], hadoop_user))
                active_datanode_count = int(
                    SSHClient(
                    host=self.config.compute.controller_nodes[0],
                    username=self.config.compute.controller_node_ssh_user,
                    pkey=self.config.compute.path_to_private_key,
                    timeout=300
                    ).exec_command(cmd))
                LOG.debug('active_datanode_count:%s' % active_datanode_count)
                print('active_datanode_count:%s' % active_datanode_count)
            except SSHExecCommandFailed as exc:
                output_msg = "Command failed."
                LOG.debug(exc)
                self.fail(output_msg)

            if not active_tasktracker_count:
                active_tasktracker_count = 0
            else:
                active_tasktracker_count = len(
                    active_tasktracker_count[:-1].split('\n')
                )
            if (
                    active_tasktracker_count == node_info['tasktracker_count']
            ) and (
                    active_datanode_count == node_info['datanode_count']
            ):
                break
            if attempt_count == 0:
                self.fail('Tasktracker or datanode cannot be started '
                          'within 5 minutes.')
            time.sleep(3)
            attempt_count -= 1

    @classmethod
    def _list_node_group_template(cls, client):
        return(client.node_group_templates.list())

    @classmethod
    def _list_cluster_templates(cls, client):
        return(client.cluster_templates.list())

    @classmethod
    def _clean_flavors(cls):
        cls._clean(cls.flavors, cls.compute_client.flavors)

    @classmethod
    def _clean_keys(cls):
        cls._clean(cls.keys, cls.compute_client.keypairs)

    @classmethod
    def _clean_cluster_templates(cls):
        cls._clean(
            cls.cluster_templates, cls.savanna_client.cluster_templates)

    @classmethod
    def _clean_clusters(cls):
        cls._clean(cls.clusters, cls.savanna_client.clusters)

    @classmethod
    def _clean_node_groups_templates(cls):
        cls._clean(cls.node_groups, cls.savanna_client.node_group_templates)

    @classmethod
    def _clean(cls, items, client):
        if items:
            for item in items:
                try:
                    client.delete(item)
                    items.remove(item)
                except RuntimeError as exc:
                    cls.error_msg.append(exc)
                    LOG.debug(exc)

    @classmethod
    def tearDownClass(cls):
        super(SavannaTest, cls).tearDownClass()
#        cls._clean_clusters()
#        cls._clean_cluster_templates()
#        cls._clean_node_groups_templates()
#        cls._clean_flavors()
#        cls._clean_keys()

