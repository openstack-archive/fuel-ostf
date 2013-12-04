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

from fuel_health.common.savanna_ssh import ssh_command

import fuel_health.nmanager as nmanager


LOG = logging.getLogger(__name__)


class SavannaTest(nmanager.OfficialClientTest):
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
        cls.neutron_floating_ip = 'net04_ext'
        cls.neutron_net = 'net04'
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
        cls.CLUSTER_CREATION_TIMEOUT = '90'
        cls.USER_KEYPAIR_ID = 'ostf_test-savanna'
        cls.PLUGIN_NAME = 'vanilla'
        cls.HADOOP_VERSION = '1.1.2'
        cls.IMAGE_NAME = 'savanna'
        cls.CLUSTER_NAME = 'ostf-test-savanna-cluster'
        cls.SAVANNA_FLAVOR = 'ostf_test-savanna-flavor'
        cls.JT_PORT = 50030
        cls.NN_PORT = 50070
        cls.TT_PORT = 50060
        cls.DN_PORT = 50075
        cls.SEC_NN_PORT = 50090

    def _test_image(self, version, plugin):
        tag_version = '_savanna_tag_%s' % version
        tag_plugin = '_savanna_tag_%s' % plugin
        LOG.debug('Testing image - plugin - %s version - %s',
                  tag_plugin, tag_version)
        for image in self.compute_client.images.list():
            if image.name == 'savanna':
                LOG.debug('Savanna image metadata is %s', image.metadata)
                if image.metadata[tag_version] == 'True'\
                    and image.metadata[tag_plugin] == 'True'\
                        and image.metadata['_savanna_username'] is not None:
                            LOG.debug('Correct image for savanna found')
                            return True
        LOG.debug('Correct image for savanna not found')
        return False

    def _create_node_group_template_and_get_id(
            self, client, name, plugin_name, hadoop_version, description,
            volumes_per_node, volume_size, node_processes, node_configs,
            floating_ip_pool=None):
        if not self.flavors:
            flavor = self.compute_client.flavors.create(self.SAVANNA_FLAVOR,
                                                        700, 1, 20)
            self.flavors.append(flavor.id)
        if floating_ip_pool:
            data = client.node_group_templates.create(
                name, plugin_name, hadoop_version, self.flavors[0],
                description, volumes_per_node, volume_size,
                node_processes, node_configs, floating_ip_pool
            )
        else:
            data = client.node_group_templates.create(
                name, plugin_name, hadoop_version, self.flavors[0],
                description, volumes_per_node, volume_size,
                node_processes, node_configs
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
            client.fail('Cluster state == \'Error\'')
        if cluster_state != 'Active':
            client.fail(
                'Cluster state != \'Active\', passed %d minutes'
                % self.CLUSTER_CREATION_TIMEOUT)

    def _get_cluster_state(self, client, cluster_id):
        data = client.clusters.get(cluster_id)
        i = 1
        while str(data.status) != 'Active':
            LOG.debug('CLUSTER STATUS:' + str(i * 10) +
                      ' sec:' + str(data.status))
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
        LOG.debug('node_ip_list_with_node_processes:\n%s',
                  node_ip_list_with_node_processes)
        return node_ip_list_with_node_processes

    def _create_cluster_and_get_info(
            self, client, plugin_name, hadoop_version, cluster_template_id,
            image_name, description, cluster_configs, node_groups,
            anti_affinity, neutron_management_network=None):
        self.keys.append(
            self.compute_client.keypairs.create(self.USER_KEYPAIR_ID))
        image_id = str(self.compute_client.images.find(name=image_name).id)
        if neutron_management_network:
            data = client.clusters.create(
                self.CLUSTER_NAME, plugin_name, hadoop_version,
                cluster_template_id, image_id, description, cluster_configs,
                node_groups, self.USER_KEYPAIR_ID, anti_affinity,
                neutron_management_network
            )
        else:
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
            self._get_cluster_node_ip_list_with_node_processes(client,
                                                               cluster_id)
        node_info = self._get_node_info(
            node_ip_list_with_node_processes, plugin_name
        )
        return {
            'cluster_id': cluster_id,
            'node_ip_list': node_ip_list_with_node_processes,
            'node_info': node_info
        }

    def _try_port(self, host, port):
        i = 0
        while True:
            cmd = ('nc -v -z -w 60 %s %s | grep succeeded' % (host, port))
            output, output_err = ssh_command(cmd)
            print('NC output after %s seconds is "%s"' % (i * 10, output))
            LOG.debug('NC output after %s seconds is "%s"',
                      i * 10, output)
            if output or str(output_err).find(' succeeded!') > 0:
                break
            if not output and i > 600:
                self.fail('On host %s port %s is not opened '
                          'more then 10 minutes' % (host, port))
            time.sleep(10)
            i += 1
        return True

    def _check_auto_assign_floating_ip(self):
        cmd_nova = ('grep auto_assign_floating_ip '
                    '/etc/nova/nova.conf | grep True')
        cmd_neutron = ('grep -E '
                       '"network_api_class=nova.network.neutronv2.api.API|'
                       'network_api_class=nova.network.quantumv2.api.API" '
                       '/etc/nova/nova.conf')
        output_nova, output_nova_err = ssh_command(cmd_nova)
        output_neutron, output_neutron_err = ssh_command(cmd_neutron)
        if output_nova or str(output_nova_err).find(' True') > 0:
            LOG.debug('auto_assign_floating_ip is found')
            return ('nova_auto', None)
        elif(output_neutron or str(output_neutron_err).find(
             'network_api_class=nova.network.neutronv2.api.API') > 0):
            LOG.debug('neutron is found')
            return ('neutron', self.neutron_floating_ip)
        else:
            LOG.debug('auto_assign_floating_ip is not found')
            LOG.debug('floating pool is %s',
                      self.compute_client.floating_ip_pools.list()[0].name)
            return ('nova',
                    self.compute_client.floating_ip_pools.list()[0].name)

    def _get_node_info(self, node_ip_list_with_node_processes, plugin_name):
        tasktracker_count = 0
        datanode_count = 0
        node_count = 0
        portmap = {
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
            portmap = {
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
            self._try_port(node_ip, '22')
            node_count += 1
            for process in processes:
                if process in portmap:
                    self._try_port(node_ip, portmap[process])
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

    def _create_cluster(self, client, cluster_template_id):
        net_type, _ = self._check_auto_assign_floating_ip()
        LOG.debug('Network type is "%s"', net_type)
        if net_type == 'neutron':
            neutron_m_network = \
                self.compute_client.networks.find(label=self.neutron_net)
            LOG.debug('Neutron network - %s', neutron_m_network.id)
            LOG.debug('Creating clister for neutron network')
            self._create_cluster_and_get_info(
                client,
                self.PLUGIN_NAME,
                self.HADOOP_VERSION,
                cluster_template_id,
                self.IMAGE_NAME,
                description='test cluster',
                cluster_configs={},
                node_groups=None,
                anti_affinity=[],
                neutron_management_network=neutron_m_network.id)
        else:
            LOG.debug('Creating clister for nova network')
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
        net_type, floating_ip_pool = self._check_auto_assign_floating_ip()
        if net_type == 'nova_auto':
            LOG.debug('Creating node group template without floating ip')
            node_group_template_tt_dn_id = \
                self._create_node_group_template_and_get_id(
                    client,
                    'ostf-test-savanna-tt-dn',
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
        else:
            LOG.debug('Creating node group template with floating ip')
            node_group_template_tt_dn_id = \
                self._create_node_group_template_and_get_id(
                    client,
                    'ostf-test-savanna-tt-dn',
                    self.plugin,
                    self.plugin_version,
                    description='test node group template',
                    volumes_per_node=0,
                    volume_size=1,
                    node_processes=['tasktracker', 'datanode'],
                    node_configs={
                        'HDFS': self.DN_CONFIG,
                        'MapReduce': self.TT_CONFIG
                    },
                    floating_ip_pool=floating_ip_pool
                )
        self.node_groups.append(node_group_template_tt_dn_id)
        return node_group_template_tt_dn_id

    def _create_node_group_template_tt_id(self, client):
        node_group_template_tt_id = \
            self._create_node_group_template_and_get_id(
                client,
                'ostf-test-savanna-tt',
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
                'ostf_test-savanna-dd',
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
            'ostf-test-savanna-cluster-template',
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
                    name='ostf-test-master-node-jt-nn',
                    flavor_id=self.flavors[0],
                    node_processes=['namenode', 'jobtracker'],
                    node_configs={
                        'HDFS': self.NN_CONFIG,
                        'MapReduce': self.JT_CONFIG
                    },
                    count=1),
                dict(
                    name='ostf-test-master-node-sec-nn',
                    flavor_id=self.flavors[0],
                    node_processes=['secondarynamenode'],
                    node_configs={
                        'HDFS': self.SNN_CONFIG
                    },
                    count=1),
                dict(
                    name='ostf-test-worker-node-tt-dn',
                    node_group_template_id=self.node_groups[0],
                    count=2),
                dict(
                    name='ostf-test-worker-node-dn',
                    node_group_template_id=self.node_groups[1],
                    count=1),
                dict(
                    name='ostf-test-worker-node-tt',
                    node_group_template_id=self.node_groups[2],
                    count=1)
            ],
            anti_affinity=[]
        )
        self.cluster_templates.append(cluster_template_id)
        return cluster_template_id

    def _create_tiny_cluster_template(self, client):
        net_type, floating_ip_pool = self._check_auto_assign_floating_ip()
        if net_type == 'nova_auto':
            LOG.debug('Creating cluster template without floating ip')
            cluster_template_id = self._create_cluster_template_and_get_id(
                client,
                'ostf-test-savanna-cluster-template',
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
                        name='ostf-test-master-node-jt-nn',
                        flavor_id=self.flavors[0],
                        node_processes=['namenode', 'jobtracker'],
                        node_configs={
                            'HDFS': self.NN_CONFIG,
                            'MapReduce': self.JT_CONFIG
                        },
                        count=1),
                    dict(
                        name='ostf-test-worker-node-tt-dn',
                        node_group_template_id=self.node_groups[0],
                        count=1),
                ],
                anti_affinity=[]
            )
        else:
            LOG.debug('Creating cluster template with floating ip')
            cluster_template_id = self._create_cluster_template_and_get_id(
                client,
                'ostf-test-savanna-cluster-template',
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
                        name='ostf-test-master-node-jt-nn',
                        flavor_id=self.flavors[0],
                        node_processes=['namenode', 'jobtracker'],
                        node_configs={
                            'HDFS': self.NN_CONFIG,
                            'MapReduce': self.JT_CONFIG
                        },
                        floating_ip_pool=floating_ip_pool,
                        count=1),
                    dict(
                        name='ostf-test-worker-node-tt-dn',
                        node_group_template_id=self.node_groups[0],
                        count=1),
                ],
                anti_affinity=[]
            )
        self.cluster_templates.append(cluster_template_id)
        return cluster_template_id

    def _await_active_workers_for_namenoded(self, node_info, plugin_name):
        attempt_count = 100
        if plugin_name == 'vanilla':
            hadoop_user = self.V_HADOOP_USER
            node_username = self.V_NODE_USERNAME
        elif plugin_name == 'hdp':
            hadoop_user = self.HDP_HADOOP_USER
        ssh_command('echo "%s" > /tmp/ostf-savanna.pem' %
                    self.keys[0].private_key)
        ssh_command('chmod 600  /tmp/ostf-savanna.pem')
        while True:
            cmd = ('ssh -i /tmp/ostf-savanna.pem -l %s '
                   '-oUserKnownHostsFile=/dev/null '
                   '-oStrictHostKeyChecking=no %s '
                   'sudo -u %s -i "hadoop job '
                   '-list-active-trackers"' %
                   (self.V_NODE_USERNAME, node_info['namenode_ip'],
                    hadoop_user))
            stdout, stderr = ssh_command(cmd)
            active_tasktracker_count = stdout
            LOG.debug('active_tasktracker_count:%s',
                      active_tasktracker_count)
            print('active_tasktracker_count:%s' % active_tasktracker_count)
            cmd = ('ssh -i /tmp/ostf-savanna.pem -l %s '
                   '-oUserKnownHostsFile=/dev/null '
                   '-oStrictHostKeyChecking=no %s '
                   'sudo -u %s -i "hadoop dfsadmin -report" '
                   '| grep "Datanodes available:.*" | awk '
                   '\'{print $3}\'' %
                   (self.V_NODE_USERNAME, node_info['namenode_ip'],
                    hadoop_user))
            stdout, stderr = ssh_command(cmd)
            active_datanode_count = stdout
            ssh.close()
            LOG.debug('active_datanode_count:%s', active_datanode_count)
            print('active_datanode_count:%s' % active_datanode_count)
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
                    items.remove(item)
                    client.delete(item)
                except RuntimeError as exc:
                    cls.error_msg.append(exc)
                    LOG.debug(exc)

    @classmethod
    def tearDownClass(cls):
        super(SavannaTest, cls).tearDownClass()
        cls._clean_clusters()
        cls._clean_cluster_templates()
        cls._clean_node_groups_templates()
        cls._clean_flavors()
        cls._clean_keys()
