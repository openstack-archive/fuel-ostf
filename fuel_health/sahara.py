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
import traceback

from novaclient import exceptions as nova_exceptions

from fuel_health.common.utils.data_utils import rand_name
import fuel_health.nmanager as nmanager


LOG = logging.getLogger(__name__)


class SaharaTest(nmanager.PlatformServicesBaseClass):

    """
    Base class for openstack sanity tests for Sahara
    """
    @classmethod
    def setUpClass(cls):
        super(SaharaTest, cls).setUpClass()

        cls.min_required_ram = 4096
        cls.max_available_ram, cls.enough_ram = (
            cls.check_compute_node_ram(cls.min_required_ram))

        if cls.manager.clients_initialized:
            cls.sg_rules = []
            cls.flavors = []
            cls.node_groups = []
            cls.cluster_templates = []
            cls.clusters = []
            cls.keys = []
            cls.plugin = 'vanilla'
            cls.plugin_version = '1.2.1'
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
            cls.HDP_NODE_USERNAME = 'root'
            cls.CLUSTER_CREATION_TIMEOUT = '90'
            cls.USER_KEYPAIR_ID = 'ostf_test-sahara-'
            cls.PLUGIN_NAME = 'vanilla'
            cls.CLUSTER_NAME = 'ostf-cluster-'
            cls.SAHARA_FLAVOR = 'ostf-test-sahara-flavor-'
            cls.JT_PORT = 50030
            cls.NN_PORT = 50070
            cls.TT_PORT = 50060
            cls.DN_PORT = 50075
            cls.SEC_NN_PORT = 50090
            # Parameters related to security group rules.
            cls.sg_name = 'default'
            cls.ip_protocol = 'tcp'
            cls.cidr = '0.0.0.0/0'
            cls.allowed_ports = [22, 50030, 50060, 50070, 50075]

    def setUp(self):
        super(SaharaTest, self).setUp()
        self.check_clients_state()
        self._add_rules_to_default_security_group()
        self._create_sahara_flavors(self.compute_client)

    def check_image(self):
        LOG.debug('Checking image for Sahara')
        image = self._find_image_by_tags(self.plugin, self.plugin_version)
        if (image is not None) and (
            '_sahara_username' in image.metadata) and (
                image.metadata['_sahara_username'] is not None):
            LOG.debug('Image with name "%s" is registered for Sahara with '
                      'username "%s"' % (image.name,
                                         image.metadata['_sahara_username']))
            return True
        LOG.debug(
            'Image is not properly registered or it is not registered at all. '
            'Correct image for Sahara not found')
        return False

    def _find_image_by_tags(self, plugin_name, plugin_version):
        tag_plugin = '_sahara_tag_%s' % plugin_name
        tag_version = '_sahara_tag_%s' % plugin_version
        for image in self.compute_client.images.list():
            if tag_plugin in image.metadata and tag_version in image.metadata:
                LOG.debug(
                    'Image with tags "%s" and "%s" found. Image name is "%s"'
                    % (plugin_name, plugin_version, image.name))
                return image
        LOG.debug('Image with tags "%s" and "%s" not found'
                  % (plugin_name, plugin_version))

    @classmethod
    def _add_rules_to_default_security_group(cls):
        # There is always default security group. Sahara always uses this
        # security group.
        for security_group in cls.compute_client.security_groups.list():
            if security_group.name == cls.sg_name:
                for port in cls.allowed_ports:
                    try:
                        rule = cls.compute_client.security_group_rules.create(
                            parent_group_id=security_group.id, from_port=port,
                            to_port=port, ip_protocol=cls.ip_protocol,
                            cidr=cls.cidr)
                    except nova_exceptions.BadRequest as exc:
                        if 'rule already exists' not in exc.message:
                            cls.fail(
                                'Failed to create "TCP" rule for port %d for '
                                'security group "%s".' % (port, cls.sg_name))
                    else:
                        cls.sg_rules.append(rule)
                return

    @classmethod
    def _create_sahara_flavors(cls, client):
        if not cls.flavors:
            cls.sahara_flavor = client.flavors.create(
                rand_name(cls.SAHARA_FLAVOR), 700, 1, 20).id
            cls.flavors.append(cls.sahara_flavor)

    @classmethod
    def _create_node_group_template(
            cls, client, name, plugin_name, plugin_version, description,
            volumes_per_node, volume_size, node_processes, node_configs,
            floating_ip_pool=None):

        body = client.node_group_templates.create(
            rand_name(name), plugin_name, plugin_version, cls.sahara_flavor,
            description, volumes_per_node, volume_size, node_processes,
            node_configs, floating_ip_pool)

        if body:
            cls.node_groups.append(body.id)
            return body

    @classmethod
    def _create_cluster_template(
            cls, client, name, plugin_name, plugin_version, description,
            cluster_configs, node_groups,  anti_affinity):

        # TODO(vrovachev): remove this loop after resolve bug:
        # https://bugs.launchpad.net/sahara/+bug/1314578
        for node_group in node_groups:
            if 'floating_ip_pool' in node_group:
                if not node_group['floating_ip_pool']:
                    del node_group['floating_ip_pool']

        body = client.cluster_templates.create(
            rand_name(name), plugin_name, plugin_version, description,
            cluster_configs, node_groups, anti_affinity)

        if body:
            cls.cluster_templates.append(body.id)
            return body

    @classmethod
    def _create_cluster(
            cls, compute_client, sahara_client, plugin_name, plugin_version,
            cluster_template_id, description, image_id, cluster_configs,
            node_groups, anti_affinity, neutron_management_network=None):

        key_name = rand_name(cls.USER_KEYPAIR_ID)
        cls.keys.append(
            compute_client.keypairs.create(key_name))

        body = sahara_client.clusters.create(
            name=rand_name(cls.CLUSTER_NAME),
            plugin_name=plugin_name,
            hadoop_version=plugin_version,
            cluster_template_id=cluster_template_id,
            default_image_id=image_id,
            description=description,
            cluster_configs=cluster_configs,
            node_groups=node_groups,
            user_keypair_id=key_name,
            anti_affinity=anti_affinity,
            net_id=neutron_management_network)

        if body:
            cls.clusters.append(body.id)
            return body

    def _check_cluster_state(self, cluster_id):

        data = self.sahara_client.clusters.get(cluster_id)
        i = 1

        while str(data.status) != 'Active':
            LOG.debug('CLUSTER STATUS:' + str(i * 10) +
                      ' sec:' + str(data.status))
            print('CLUSTER STATUS:' + str(i * 10) + ' sec:' + str(data.status))

            if str(data.status) == 'Error':
                LOG.debug('\n' + str(i * 10) + ' sec:' + str(data) + '\n')
                self.fail("Cluster state == 'Error'")

            if i > self.CLUSTER_CREATION_TIMEOUT * 6:
                LOG.debug('\n' + str(i * 10) + ' sec:' + str(data) + '\n')
                self.fail(
                    'Cluster state != \'Active\', passed {timeout} '
                    'minutes'.format(timeout=self.CLUSTER_CREATION_TIMEOUT))

            data = self.sahara_client.clusters.get(cluster_id)
            time.sleep(10)
            i += 1

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
            self, plugin_name, plugin_version, cluster_template_id,
            description, cluster_configs, node_groups, anti_affinity,
            neutron_management_network=None):

        image_name = self._find_image_by_tags(plugin_name, plugin_version).name
        image_id = self.compute_client.images.find(name=image_name).id

        body = self._create_cluster(
            self.compute_client, self.sahara_client, plugin_name,
            plugin_version, cluster_template_id, description, image_id,
            cluster_configs, node_groups, anti_affinity,
            neutron_management_network)

        self._check_cluster_state(body.id)

        node_ip_list_with_node_processes = \
            self._get_cluster_node_ip_list_with_node_processes(
                self.sahara_client, body.id)

        node_info = self._get_node_info(
            node_ip_list_with_node_processes, plugin_name)

        self._await_active_workers_for_namenoded(node_info, plugin_name)

        return {
            'cluster_id': body.id,
            'node_ip_list': node_ip_list_with_node_processes,
            'node_info': node_info
        }

    def _check_auto_assign_floating_ip(self):
        cmd_nova = ('grep auto_assign_floating_ip '
                    '/etc/nova/nova.conf | grep True')
        cmd_neutron = ('grep -E '
                       '"network_api_class=nova.network.neutronv2.api.API" '
                       '/etc/nova/nova.conf')
        output_nova, output_nova_err = self._run_ssh_cmd(cmd_nova)
        output_neutron, output_neutron_err = self._run_ssh_cmd(cmd_neutron)
        if(output_neutron or str(output_neutron_err).find(
                'network_api_class=nova.network.neutronv2.api.API') > 0):
            LOG.debug('neutron is found')
            network = self.compute_client.networks.find(
                label=self.neutron_floating_ip)
            return ('neutron', network.id)
        elif output_nova or str(output_nova_err).find(' True') > 0:
            LOG.debug('auto_assign_floating_ip is found')
            return ('nova_auto', None)
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

    def create_sahara_cluster(self, cluster_template_id):

        net_type, _ = self._check_auto_assign_floating_ip()
        LOG.debug('Network type is "%s"', net_type)

        neutron_m_network_id = None
        if net_type == 'neutron':
            neutron_m_network_id = \
                self.compute_client.networks.find(label=self.neutron_net).id
            LOG.debug('Neutron network - %s', neutron_m_network_id)
            LOG.debug('Creating cluster for neutron network')

        return self._create_cluster_and_get_info(
            self.PLUGIN_NAME,
            self.plugin_version,
            cluster_template_id,
            description='test cluster',
            cluster_configs={},
            node_groups=None,
            anti_affinity=[],
            neutron_management_network=neutron_m_network_id)

    def create_node_group_template_tt_dn(self):

        net_type, floating_ip_pool = self._check_auto_assign_floating_ip()

        if net_type == 'nova_auto':
            LOG.debug('Creating node group template without floating ip')
        else:
            LOG.debug('Creating node group template with floating ip')

        return self._create_node_group_template(
            self.sahara_client,
            'ostf-test-sahara-tt-dn-',
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
            floating_ip_pool=floating_ip_pool)

    def create_node_group_template_tt(self):

        net_type, floating_ip_pool = self._check_auto_assign_floating_ip()

        if net_type == 'nova_auto':
            LOG.debug('Creating node group template without floating ip')
        else:
            LOG.debug('Creating node group template with floating ip')

        return self._create_node_group_template(
            self.sahara_client,
            'ostf-test-sahara-tt-',
            self.plugin,
            self.plugin_version,
            description='test node group template',
            volumes_per_node=0,
            volume_size=0,
            node_processes=['tasktracker'],
            node_configs={
                'MapReduce': self.TT_CONFIG
            },
            floating_ip_pool=floating_ip_pool)

    def create_node_group_template_dn(self):

        net_type, floating_ip_pool = self._check_auto_assign_floating_ip()

        if net_type == 'nova_auto':
            LOG.debug('Creating node group template without floating ip')
        else:
            LOG.debug('Creating node group template with floating ip')

        return self._create_node_group_template(
            self.sahara_client,
            'ostf-test-sahara-dn-',
            self.plugin,
            self.plugin_version,
            description='test node group template',
            volumes_per_node=0,
            volume_size=0,
            node_processes=['datanode'],
            node_configs={
                'MapReduce': self.TT_CONFIG
            },
            floating_ip_pool=floating_ip_pool)

    def create_cluster_template(self):
        return self._create_cluster_template(
            self.sahara_client,
            'ostf-test-sahara-cluster-template-',
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
                    flavor_id=self.sahara_flavor,
                    node_processes=['namenode', 'jobtracker'],
                    node_configs={
                        'HDFS': self.NN_CONFIG,
                        'MapReduce': self.JT_CONFIG
                    },
                    count=1),
                dict(
                    name='ostf-test-master-node-sec-nn',
                    flavor_id=self.sahara_flavor,
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
            anti_affinity=[])

    def create_tiny_cluster_template(self):

        net_type, floating_ip_pool = self._check_auto_assign_floating_ip()

        if net_type == 'nova_auto':
            LOG.debug('Creating cluster template without floating ip')
        else:
            LOG.debug('Creating cluster template with floating ip')

        return self._create_cluster_template(
            self.sahara_client,
            'ostf-sahara-cl-tmpl-',
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
                    name='ostf-test-master',
                    flavor_id=self.sahara_flavor,
                    node_processes=['namenode', 'jobtracker'],
                    node_configs={
                        'HDFS': self.NN_CONFIG,
                        'MapReduce': self.JT_CONFIG
                    },
                    floating_ip_pool=floating_ip_pool,
                    count=1),
                dict(
                    name='ostf-test-worker',
                    node_group_template_id=self.node_groups[0],
                    count=1),
            ],
            anti_affinity=[]
        )

    def _await_active_workers_for_namenoded(self, node_info, plugin_name):
        attempt_count = 100
        if plugin_name == 'vanilla':
            hadoop_user = self.V_HADOOP_USER
            node_username = self.V_NODE_USERNAME
        elif plugin_name == 'hdp':
            hadoop_user = self.HDP_HADOOP_USER
            node_username = self.HDP_NODE_USERNAME
        self._run_ssh_cmd('echo "%s" > /tmp/ostf-sahara.pem' %
                          self.keys[0].private_key)
        self._run_ssh_cmd('chmod 600  /tmp/ostf-sahara.pem')
        while True:
            cmd = ('ssh -i /tmp/ostf-sahara.pem -l %s '
                   '-oUserKnownHostsFile=/dev/null '
                   '-oStrictHostKeyChecking=no %s '
                   'sudo -u %s -i "hadoop job '
                   '-list-active-trackers | wc -l"' %
                   (node_username, node_info['namenode_ip'],
                    hadoop_user))
            stdout, stderr = self._run_ssh_cmd(cmd)
            active_tasktracker_count = int(stdout)
            LOG.debug('active_tasktracker_count:%s',
                      active_tasktracker_count)
            print('active_tasktracker_count:%s' % active_tasktracker_count)
            cmd = ('ssh -i /tmp/ostf-sahara.pem -l %s '
                   '-oUserKnownHostsFile=/dev/null '
                   '-oStrictHostKeyChecking=no %s '
                   'sudo -u %s -i "hadoop dfsadmin -report" '
                   '| grep "Datanodes available:.*" | awk '
                   '\'{print $3}\'' %
                   (node_username, node_info['namenode_ip'],
                    hadoop_user))
            stdout, stderr = self._run_ssh_cmd(cmd)
            active_datanode_count = int(stdout)
            LOG.debug('active_datanode_count:%s', active_datanode_count)
            print('active_datanode_count:%s' % active_datanode_count)

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
    def _list_node_group_template(cls):
        return cls.sahara_client.node_group_templates.list()

    @classmethod
    def _list_cluster_templates(cls):
        return cls.sahara_client.cluster_templates.list()

    @classmethod
    def _clean_security_group_rules(cls):
        cls._clean(cls.sg_rules, cls.compute_client.security_group_rules)

    @classmethod
    def _clean_flavors(cls):
        cls._clean(cls.flavors, cls.compute_client.flavors)

    @classmethod
    def _clean_keys(cls):
        cls._clean(cls.keys, cls.compute_client.keypairs)

    @classmethod
    def _clean_cluster_templates(cls):
        cls._clean(
            cls.cluster_templates, cls.sahara_client.cluster_templates)

    @classmethod
    def _clean_clusters(cls):
        cls._clean(cls.clusters, cls.sahara_client.clusters)

    @classmethod
    def _clean_node_groups_templates(cls):
        cls._clean(cls.node_groups, cls.sahara_client.node_group_templates)

    @classmethod
    def _clean(cls, items, client):
        if items:
            for item in items[:]:
                try:
                    client.delete(item)
                    items.remove(item)
                except RuntimeError as exc:
                    cls.error_msg.append(exc)
                    LOG.debug(traceback.format_exc())

    @classmethod
    def tearDownClass(cls):
        if cls.manager.clients_initialized:
            cls._clean_clusters()
            cls._clean_cluster_templates()
            cls._clean_node_groups_templates()
            cls._clean_security_group_rules()
            cls._clean_flavors()
            cls._clean_keys()
        super(SaharaTest, cls).tearDownClass()
