# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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
from __future__ import print_function

import os
import sys
import traceback
import unittest2

import keystoneclient
from oslo.config import cfg
import requests

from fuel_health.common import log as logging
from fuel_health import exceptions


LOG = logging.getLogger(__name__)

identity_group = cfg.OptGroup(name='identity',
                              title="Keystone Configuration Options")

IdentityGroup = [
    cfg.StrOpt('catalog_type',
               default='identity',
               help="Catalog type of the Identity service."),
    cfg.BoolOpt('disable_ssl_certificate_validation',
                default=False,
                help="Set to True if using self-signed SSL certificates."),
    cfg.StrOpt('uri',
               default='http://localhost/',
               help="Full URI of the OpenStack Identity API (Keystone), v2"),
    cfg.StrOpt('uri_v3',
               help='Full URI of the OpenStack Identity API (Keystone), v3'),
    cfg.StrOpt('strategy',
               default='keystone',
               help="Which auth method does the environment use? "
                    "(basic|keystone)"),
    cfg.StrOpt('region',
               default='RegionOne',
               help="The identity region name to use."),
    cfg.StrOpt('admin_username',
               default='nova',
               help="Administrative Username to use for"
                    "Keystone API requests."),
    cfg.StrOpt('admin_tenant_name',
               default='service',
               help="Administrative Tenant name to use for Keystone API "
                    "requests."),
    cfg.StrOpt('admin_password',
               default='nova',
               help="API key to use when authenticating as admin.",
               secret=True),
]


def register_identity_opts(conf):
    conf.register_group(identity_group)
    for opt in IdentityGroup:
        conf.register_opt(opt, group='identity')

master_node_group = cfg.OptGroup(name='master',
                                 title='Master Node Options')

MasterGroup = [
    cfg.StrOpt('keystone_password',
               default='admin',
               help='Default keystone password on master node'),
    cfg.StrOpt('keystone_user',
               default='admin',
               help='Default keystone user on master node'),
    cfg.StrOpt('master_node_ssh_user',
               default='root'),
    cfg.StrOpt('master_node_ssh_password',
               default='r00tme',
               help='ssh user pass of master node'),
    cfg.IntOpt('ssh_timeout',
               default=50,
               help="Timeout in seconds to wait for authentication to "
                    "succeed."),
]


def register_master_opts(conf):
    conf.register_group(master_node_group)
    for opt in MasterGroup:
        conf.register_opt(opt, group='master')

compute_group = cfg.OptGroup(name='compute',
                             title='Compute Service Options')

ComputeGroup = [
    cfg.BoolOpt('allow_tenant_isolation',
                default=False,
                help="Allows test cases to create/destroy tenants and "
                     "users. This option enables isolated test cases and "
                     "better parallel execution, but also requires that "
                     "OpenStack Identity API admin credentials are known."),
    cfg.BoolOpt('allow_tenant_reuse',
                default=True,
                help="If allow_tenant_isolation is True and a tenant that "
                     "would be created for a given test already exists (such "
                     "as from a previously-failed run), re-use that tenant "
                     "instead of failing because of the conflict. Note that "
                     "this would result in the tenant being deleted at the "
                     "end of a subsequent successful run."),
    cfg.StrOpt('image_ssh_user',
               default="root",
               help="User name used to authenticate to an instance."),
    cfg.StrOpt('image_alt_ssh_user',
               default="root",
               help="User name used to authenticate to an instance using "
                    "the alternate image."),
    cfg.BoolOpt('create_image_enabled',
                default=True,
                help="Does the test environment support snapshots?"),
    cfg.IntOpt('build_interval',
               default=10,
               help="Time in seconds between build status checks."),
    cfg.IntOpt('build_timeout',
               default=500,
               help="Timeout in seconds to wait for an instance to build."),
    cfg.BoolOpt('run_ssh',
                default=False,
                help="Does the test environment support snapshots?"),
    cfg.StrOpt('ssh_user',
               default='root',
               help="User name used to authenticate to an instance."),
    cfg.IntOpt('ssh_timeout',
               default=50,
               help="Timeout in seconds to wait for authentication to "
                    "succeed."),
    cfg.IntOpt('ssh_channel_timeout',
               default=20,
               help="Timeout in seconds to wait for output from ssh "
                    "channel."),
    cfg.IntOpt('ip_version_for_ssh',
               default=4,
               help="IP version used for SSH connections."),
    cfg.StrOpt('catalog_type',
               default='compute',
               help="Catalog type of the Compute service."),
    cfg.StrOpt('path_to_private_key',
               default='/root/.ssh/id_rsa',
               help="Path to a private key file for SSH access to remote "
                    "hosts"),
    cfg.ListOpt('controller_nodes',
                default=[],
                help="IP addresses of controller nodes"),
    cfg.ListOpt('controller_names',
                default=[],
                help="FQDNs of controller nodes"),
    cfg.ListOpt('online_controllers',
                default=[],
                help="ips of online controller nodes"),
    cfg.ListOpt('online_controller_names',
                default=[],
                help="FQDNs of online controller nodes"),
    cfg.ListOpt('compute_nodes',
                default=[],
                help="IP addresses of compute nodes"),
    cfg.ListOpt('online_computes',
                default=[],
                help="IP addresses of online compute nodes"),
    cfg.ListOpt('ceph_nodes',
                default=[],
                help="IP addresses of nodes with ceph-osd role"),
    cfg.StrOpt('controller_node_ssh_user',
               default='root',
               help="ssh user of one of the controller nodes"),
    cfg.StrOpt('amqp_pwd',
               default='root',
               help="amqp_pwd"),
    cfg.StrOpt('controller_node_ssh_password',
               default='r00tme',
               help="ssh user pass of one of the controller nodes"),
    cfg.StrOpt('image_name',
               default="TestVM",
               help="Valid secondary image reference to be used in tests."),
    cfg.StrOpt('deployment_mode',
               default="ha",
               help="Deployments mode"),
    cfg.StrOpt('deployment_os',
               default="RHEL",
               help="Deployments os"),
    cfg.IntOpt('flavor_ref',
               default=42,
               help="Valid primary flavor to use in tests."),
    cfg.StrOpt('libvirt_type',
               default='qemu',
               help="Type of hypervisor to use."),
]


def register_compute_opts(conf):
    conf.register_group(compute_group)
    for opt in ComputeGroup:
        conf.register_opt(opt, group='compute')

image_group = cfg.OptGroup(name='image',
                           title="Image Service Options")

ImageGroup = [
    cfg.StrOpt('api_version',
               default='1',
               help="Version of the API"),
    cfg.StrOpt('catalog_type',
               default='image',
               help='Catalog type of the Image service.'),
    cfg.StrOpt('http_image',
               default='http://download.cirros-cloud.net/0.3.1/'
                       'cirros-0.3.1-x86_64-uec.tar.gz',
               help='http accessable image')
]


def register_image_opts(conf):
    conf.register_group(image_group)
    for opt in ImageGroup:
        conf.register_opt(opt, group='image')


network_group = cfg.OptGroup(name='network',
                             title='Network Service Options')

NetworkGroup = [
    cfg.StrOpt('catalog_type',
               default='network',
               help='Catalog type of the Network service.'),
    cfg.StrOpt('tenant_network_cidr',
               default="10.100.0.0/16",
               help="The cidr block to allocate tenant networks from"),
    cfg.StrOpt('network_provider',
               default="nova_network",
               help="Value of network provider"),
    cfg.IntOpt('tenant_network_mask_bits',
               default=29,
               help="The mask bits for tenant networks"),
    cfg.BoolOpt('tenant_networks_reachable',
                default=True,
                help="Whether tenant network connectivity should be "
                     "evaluated directly"),
    cfg.BoolOpt('neutron_available',
                default=False,
                help="Whether or not neutron is expected to be available"),
]


def register_network_opts(conf):
    conf.register_group(network_group)
    for opt in NetworkGroup:
        conf.register_opt(opt, group='network')


volume_group = cfg.OptGroup(name='volume',
                            title='Block Storage Options')

VolumeGroup = [
    cfg.IntOpt('build_interval',
               default=10,
               help='Time in seconds between volume availability checks.'),
    cfg.IntOpt('build_timeout',
               default=180,
               help='Timeout in seconds to wait for a volume to become'
                    'available.'),
    cfg.StrOpt('catalog_type',
               default='volume',
               help="Catalog type of the Volume Service"),
    cfg.BoolOpt('cinder_node_exist',
                default=True,
                help="Allow to run tests if cinder exist"),
    cfg.BoolOpt('cinder_vmware_node_exist',
                default=True,
                help="Allow to run tests if cinder-vmware exist"),
    cfg.BoolOpt('ceph_exist',
                default=True,
                help="Allow to run tests if ceph exist"),
    cfg.BoolOpt('multi_backend_enabled',
                default=False,
                help="Runs Cinder multi-backend test (requires 2 backends)"),
    cfg.StrOpt('backend1_name',
               default='BACKEND_1',
               help="Name of the backend1 (must be declared in cinder.conf)"),
    cfg.StrOpt('backend2_name',
               default='BACKEND_2',
               help="Name of the backend2 (must be declared in cinder.conf)"),
    cfg.StrOpt('cinder_vmware_storage_az',
               default='vcenter',
               help="Name of storage availability zone for cinder-vmware."),
]


def register_volume_opts(conf):
    conf.register_group(volume_group)
    for opt in VolumeGroup:
        conf.register_opt(opt, group='volume')


object_storage_group = cfg.OptGroup(name='object-storage',
                                    title='Object Storage Service Options')

ObjectStoreConfig = [
    cfg.StrOpt('catalog_type',
               default='object-store',
               help="Catalog type of the Object-Storage service."),
    cfg.StrOpt('container_sync_timeout',
               default=120,
               help="Number of seconds to time on waiting for a container"
                    "to container synchronization complete."),
    cfg.StrOpt('container_sync_interval',
               default=5,
               help="Number of seconds to wait while looping to check the"
                    "status of a container to container synchronization"),
]


def register_object_storage_opts(conf):
    conf.register_group(object_storage_group)
    for opt in ObjectStoreConfig:
        conf.register_opt(opt, group='object-storage')


sahara = cfg.OptGroup(name='sahara',
                      title='Sahara Service Options')

SaharaConfig = [
    cfg.StrOpt('api_url',
               default='10.20.0.131',
               help="IP of sahara service."),
    cfg.StrOpt('port',
               default=8386,
               help="Port of sahara service."),
    cfg.StrOpt('api_version',
               default='1.1',
               help="API version of sahara service."),
    cfg.StrOpt('plugin',
               default='vanilla',
               help="Plugin name of sahara service."),
    cfg.StrOpt('plugin_version',
               default='1.1.2',
               help="Plugin version of sahara service."),
    cfg.StrOpt('tt_config',
               default={'Task Tracker Heap Size': 515},
               help="Task Tracker config  of sahara service."),
]


def register_sahara_opts(conf):
    conf.register_group(sahara)
    for opt in SaharaConfig:
        conf.register_opt(opt, group='sahara')


murano_group = cfg.OptGroup(name='murano',
                            title='Murano API Service Options')

MuranoConfig = [
    cfg.StrOpt('api_url',
               default=None,
               help="Murano API Service URL."),
    cfg.StrOpt('api_url_management',
               default=None,
               help="Murano API Service management URL."),
    cfg.BoolOpt('insecure',
                default=False,
                help="This parameter allow to enable SSL encription"),
    cfg.StrOpt('agListnerIP',
               default='10.100.0.155',
               help="Murano SQL Cluster AG IP."),
    cfg.StrOpt('clusterIP',
               default='10.100.0.150',
               help="Murano SQL Cluster IP."),
]


def register_murano_opts(conf):
    conf.register_group(murano_group)
    for opt in MuranoConfig:
        conf.register_opt(opt, group='murano')


heat_group = cfg.OptGroup(name='heat',
                          title='Heat Options')

HeatConfig = [
    cfg.StrOpt('endpoint',
               default=None,
               help="Heat API Service URL."),
]


fuel_group = cfg.OptGroup(name='fuel',
                          title='Fuel options')

FuelConf = [
    cfg.StrOpt('fuel_version',
               default=None,
               help="Fuel version"),
    cfg.StrOpt('dns',
               default=None,
               help="dns"),
]


def register_fuel_opts(conf):
    conf.register_group(fuel_group)
    [conf.register_opt(opt, group='fuel') for opt in FuelConf]


def register_heat_opts(conf):
    conf.register_group(heat_group)
    for opt in HeatConfig:
        conf.register_opt(opt, group='heat')


def process_singleton(cls):
    """Wrapper for classes... To be instantiated only one time per process."""
    instances = {}

    def wrapper(*args, **kwargs):
        LOG.info('INSTANCE %s' % instances)
        pid = os.getpid()
        if pid not in instances:
            instances[pid] = cls(*args, **kwargs)
        return instances[pid]

    return wrapper


@process_singleton
class FileConfig(object):
    """Provides OpenStack configuration information."""

    DEFAULT_CONFIG_DIR = os.path.join(os.path.abspath(
        os.path.dirname(__file__)), 'etc')

    DEFAULT_CONFIG_FILE = "test.conf"

    def __init__(self):
        """Initialize a configuration from a conf directory and conf file."""
        config_files = []

        failsafe_path = "/etc/fuel/" + self.DEFAULT_CONFIG_FILE

        # Environment variables override defaults...
        custom_config = os.environ.get('CUSTOM_FUEL_CONFIG')
        LOG.info('CUSTOM CONFIG PATH %s' % custom_config)
        if custom_config:
            path = custom_config
        else:
            conf_dir = os.environ.get('FUEL_CONFIG_DIR',
                                      self.DEFAULT_CONFIG_DIR)
            conf_file = os.environ.get('FUEL_CONFIG', self.DEFAULT_CONFIG_FILE)

            path = os.path.join(conf_dir, conf_file)

            if not (os.path.isfile(path) or 'FUEL_CONFIG_DIR'
                    in os.environ or 'FUEL_CONFIG' in os.environ):
                path = failsafe_path

        LOG.info("Using fuel config file %s" % path)

        if not os.path.exists(path):
            msg = "Config file {0} not found".format(path)
            print(RuntimeError(msg), file=sys.stderr)
        else:
            config_files.append(path)

        cfg.CONF([], project='fuel', default_config_files=config_files)

        register_compute_opts(cfg.CONF)
        register_identity_opts(cfg.CONF)
        register_network_opts(cfg.CONF)
        register_master_opts(cfg.CONF)
        register_volume_opts(cfg.CONF)
        register_murano_opts(cfg.CONF)
        register_heat_opts(cfg.CONF)
        register_sahara_opts(cfg.CONF)
        register_fuel_opts(cfg.CONF)
        self.compute = cfg.CONF.compute
        self.identity = cfg.CONF.identity
        self.network = cfg.CONF.network
        self.master = cfg.CONF.master
        self.volume = cfg.CONF.volume
        self.murano = cfg.CONF.murano
        self.heat = cfg.CONF.heat
        self.sahara = cfg.CONF.sahara
        self.fuel = cfg.CONF.fuel


class ConfigGroup(object):
    # USE SLOTS

    def __init__(self, opts):
        self.parse_opts(opts)

    def parse_opts(self, opts):
        for opt in opts:
            name = opt.name
            self.__dict__[name] = opt.default

    def __setattr__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem(self, key, value):
        self.__dict__[key] = value

    def __repr__(self):
        return u"{0} WITH {1}".format(
            self.__class__.__name__,
            self.__dict__)


@process_singleton
class NailgunConfig(object):

    identity = ConfigGroup(IdentityGroup)
    compute = ConfigGroup(ComputeGroup)
    image = ConfigGroup(ImageGroup)
    master = ConfigGroup(MasterGroup)
    network = ConfigGroup(NetworkGroup)
    volume = ConfigGroup(VolumeGroup)
    object_storage = ConfigGroup(ObjectStoreConfig)
    murano = ConfigGroup(MuranoConfig)
    sahara = ConfigGroup(SaharaConfig)
    heat = ConfigGroup(HeatConfig)
    fuel = ConfigGroup(FuelConf)

    def __init__(self, parse=True):
        LOG.info('INITIALIZING NAILGUN CONFIG')
        self.nailgun_host = os.environ.get('NAILGUN_HOST', None)
        self.nailgun_port = os.environ.get('NAILGUN_PORT', None)
        self.nailgun_url = 'http://{0}:{1}'.format(self.nailgun_host,
                                                   self.nailgun_port)
        token = os.environ.get('NAILGUN_TOKEN')
        self.cluster_id = os.environ.get('CLUSTER_ID', None)
        self.req_session = requests.Session()
        self.req_session.trust_env = False
        if token:
            self.req_session.headers.update({'X-Auth-Token': token})
        if parse:
            self.prepare_config()

    def prepare_config(self, *args, **kwargs):
        try:
            self._parse_meta()
            LOG.info('parse meta successful')
            self._parse_cluster_attributes()
            LOG.info('parse cluster attr successful')
            self._parse_nodes_cluster_id()
            LOG.info('parse node cluster successful')
            self._parse_networks_configuration()
            LOG.info('parse network configuration successful')
            self.set_endpoints()
            LOG.info('set endpoints successful')
            self.set_proxy()
            LOG.info('set proxy successful')
            self._parse_cluster_generated_data()
            LOG.info('parse generated successful')
            self._parse_vmware_attributes()
            LOG.info('parse vmware attributes successful')
        except exceptions.SetProxy as exc:
            raise exc
        except Exception:
            LOG.warning('Something wrong with endpoints')
            LOG.debug(traceback.format_exc())

    def _parse_cluster_attributes(self):
        api_url = '/api/clusters/%s/attributes' % self.cluster_id
        response = self.req_session.get(self.nailgun_url + api_url)
        LOG.info('RESPONSE %s STATUS %s' % (api_url, response.status_code))
        data = response.json()
        LOG.info('RESPONSE FROM %s - %s' % (api_url, data))
        access_data = data['editable']['access']
        common_data = data['editable']['common']

        self.identity.admin_tenant_name = \
            (
                os.environ.get('OSTF_OS_TENANT_NAME') or
                access_data['tenant']['value']
            )
        self.identity.admin_username = \
            (
                os.environ.get('OSTF_OS_USERNAME') or
                access_data['user']['value']
            )
        self.identity.admin_password = \
            (
                os.environ.get('OSTF_OS_PASSWORD') or
                access_data['password']['value']
            )
        self.compute.libvirt_type = common_data['libvirt_type']['value']
        self.compute.use_vcenter = common_data['use_vcenter']['value']
        self.compute.auto_assign_floating_ip = common_data[
            'auto_assign_floating_ip']['value']

        api_url = '/api/clusters/%s' % self.cluster_id
        cluster_data = self.req_session.get(self.nailgun_url + api_url).json()
        network_provider = cluster_data.get('net_provider', 'nova_network')
        self.network.network_provider = network_provider
        release_id = cluster_data.get('release_id', 'failed to get id')
        self.fuel.fuel_version = cluster_data.get(
            'fuel_version', 'failed to get fuel version')
        LOG.info('Release id is {0}'.format(release_id))
        release_data = self.req_session.get(
            self.nailgun_url + '/api/releases/{0}'.format(release_id)).json()
        deployment_os = release_data.get(
            'operating_system', 'failed to get os')
        LOG.info('Deployment os is {0}'.format(deployment_os))
        if deployment_os != 'RHEL':
            storage = data['editable']['storage']['volumes_ceph']['value']
            self.volume.ceph_exist = storage
        self.fuel.dns = data['editable']['external_dns'].get('value', None)

    def _parse_nodes_cluster_id(self):
        api_url = '/api/nodes?cluster_id=%s' % self.cluster_id
        response = self.req_session.get(self.nailgun_url + api_url)
        LOG.info('RESPONSE %s STATUS %s' % (api_url, response.status_code))
        data = response.json()
        # to make backward compatible
        if 'objects' in data:
            data = data['objects']
        controller_nodes = filter(lambda node: 'controller' in node['roles'],
                                  data)
        online_controllers = filter(
            lambda node: 'controller' in node['roles'] and
                         node['online'] is True, data)
        cinder_nodes = filter(lambda node: 'cinder' in node['roles'],
                              data)
        cinder_vmware_nodes = filter(lambda node: 'cinder-vmware' in
                                     node['roles'], data)
        controller_ips = []
        controller_names = []
        public_ips = []
        online_controllers_ips = []
        online_controller_names = []
        for node in controller_nodes:
            public_network = next(network for network in node['network_data']
                                  if network['name'] == 'public')
            ip = public_network['ip'].split('/')[0]
            public_ips.append(ip)
            controller_ips.append(node['ip'])
            controller_names.append(node['fqdn'])
        LOG.info("IP %s NAMES %s" % (controller_ips, controller_names))

        for node in online_controllers:
            online_controllers_ips.append(node['ip'])
            online_controller_names.append(node['fqdn'])
        LOG.info("Online controllers ips is %s" % online_controllers_ips)

        self.compute.nodes = data
        self.compute.public_ips = public_ips
        self.compute.controller_nodes = controller_ips
        self.compute.controller_names = controller_names
        self.compute.online_controllers = online_controllers_ips
        self.compute.online_controller_names = online_controller_names
        if not cinder_nodes:
            self.volume.cinder_node_exist = False
        if not cinder_vmware_nodes:
            self.volume.cinder_vmware_node_exist = False

        compute_nodes = filter(lambda node: 'compute' in node['roles'],
                               data)
        online_computes = filter(
            lambda node: 'compute' in node['roles']
            and node['online'] is True, data)
        online_computes_ips = []
        for node in online_computes:
            online_computes_ips.append(node['ip'])
        LOG.info('Online compute ips is {0}'.format(online_computes_ips))
        self.compute.online_computes = online_computes_ips
        compute_ips = []
        for node in compute_nodes:
            compute_ips.append(node['ip'])
        LOG.info("COMPUTES IPS %s" % compute_ips)
        self.compute.compute_nodes = compute_ips
        ceph_nodes = filter(lambda node: 'ceph-osd' in node['roles'],
                            data)
        self.compute.ceph_nodes = ceph_nodes

    def _parse_meta(self):
        api_url = '/api/clusters/%s' % self.cluster_id
        data = self.req_session.get(self.nailgun_url + api_url).json()
        self.mode = data['mode']
        self.compute.deployment_mode = self.mode
        release_id = data.get('release_id', 'failed to get id')
        LOG.info('Release id is {0}'.format(release_id))
        release_data = self.req_session.get(
            self.nailgun_url + '/api/releases/{0}'.format(release_id)).json()
        self.compute.deployment_os = release_data.get(
            'operating_system', 'failed to get os')
        self.compute.release_version = release_data.get(
            'version', 'failed to get release version')

    def _parse_networks_configuration(self):
        api_url = '/api/clusters/{0}/network_configuration/{1}'.format(
            self.cluster_id, self.network.network_provider)
        data = self.req_session.get(self.nailgun_url + api_url).json()
        self.network.raw_data = data

    def _parse_cluster_generated_data(self):
        api_url = '/api/clusters/%s/generated' % self.cluster_id
        data = self.req_session.get(self.nailgun_url + api_url).json()
        self.generated_data = data
        amqp_data = data['rabbit']
        self.amqp_pwd = amqp_data['password']
        if 'RHEL' in self.compute.deployment_os:
            storage = data['storage']['volumes_ceph']
            self.volume.ceph_exist = storage

    def _parse_ostf_api(self):
        api_url = '/api/ostf/%s' % self.cluster_id
        response = self.req_session.get(self.nailgun_url + api_url)
        data = response.json()
        self.identity.url = data['horizon_url'] + 'dashboard'
        self.identity.uri = data['keystone_url'] + 'v2.0/'

    def _parse_vmware_attributes(self):
        if self.volume.cinder_vmware_node_exist:
            api_url = '/api/clusters/%s/vmware_attributes' % self.cluster_id
            data = self.req_session.get(self.nailgun_url + api_url).json()
            az = data['editable']['value']['availability_zones'][0]['az_name']
            self.volume.cinder_vmware_storage_az = "{0}-cinder".format(az)

    def find_proxy(self, ip):

        if 'service_endpoint' in self.network.raw_data:
            keystone_vip = self.network.raw_data['service_endpoint']
        else:
            keystone_vip = self.network.raw_data.get('management_vip', None)

        auth_url = 'http://{0}:{1}/{2}/'.format(keystone_vip, 5000, 'v2.0')

        try:
            os.environ['http_proxy'] = 'http://{0}:{1}'.format(ip, 8888)
            LOG.warning('Try to check proxy on {0}'.format(ip))
            keystoneclient.v2_0.client.Client(
                username=self.identity.admin_username,
                password=self.identity.admin_password,
                tenant_name=self.identity.admin_tenant_name,
                auth_url=auth_url,
                insecure=False)
            return ip
        except Exception:
            LOG.warning('Can not pass authorization '
                        'with proxy on {0}'.format(ip))
            LOG.debug(traceback.format_exc())

    def set_proxy(self):
        """Sets environment property for http_proxy:
            To behave properly - method must be called after all nailgun params
            is processed
        """
        if not self.compute.online_controllers:
            raise exceptions.OfflineControllers()

        proxies = [self.find_proxy(ip) for ip in
                   self.compute.online_controllers]
        if not proxies:
            raise exceptions.SetProxy()

        os.environ['http_proxy'] = 'http://{0}:{1}'.format(proxies[0], 8888)

    def set_endpoints(self):
        # NOTE(dshulyak) this is hacky convention to allow granular deployment
        # of keystone
        if 'service_endpoint' in self.network.raw_data:
            keystone_vip = self.network.raw_data['service_endpoint']
            management_vip = self.network.raw_data.get('management_vip', None)
        else:
            management_vip = self.network.raw_data.get('management_vip', None)
            keystone_vip = management_vip
        public_vip = self.network.raw_data.get('public_vip', None)
        # workaround for api without management_vip for ha mode
        if not keystone_vip and 'ha' in self.mode:
            self._parse_ostf_api()
        else:
            endpoint = keystone_vip or self.compute.public_ips[0]
            endpoint_mur_sav = management_vip \
                or self.compute.controller_nodes[0]
            self.horizon_url = 'http://{0}/{1}/'.format(
                public_vip, 'dashboard')
            self.horizon_ubuntu_url = 'http://{0}/'.format(public_vip)
            self.identity.uri = 'http://{0}:{1}/{2}/'.format(
                endpoint, 5000, 'v2.0')
            self.murano.api_url = 'http://{0}:{1}'.format(
                endpoint_mur_sav, 8082)
            self.sahara.api_url = 'http://{0}:{1}/{2}'.format(
                endpoint_mur_sav, 8386, 'v1.0')
            self.heat.endpoint = 'http://{0}:{1}/{2}'.format(
                endpoint_mur_sav, 8004, 'v1')


def FuelConfig():
    if 'CUSTOM_FUEL_CONFIG' in os.environ:
        return FileConfig()
    else:
        try:
            return NailgunConfig()
        except exceptions.SetProxy as e:
            raise unittest2.TestCase.failureException(str(e))
