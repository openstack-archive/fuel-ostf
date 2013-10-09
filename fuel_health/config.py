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

import os
import sys

from oslo.config import cfg
import requests

from fuel_health.common import log as logging


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
    cfg.StrOpt('url',
               default='http://localhost:5000/v2.0/',
               help="Dashboard Openstack url, v2"),
    cfg.StrOpt('ubuntu_url',
               default='http://localhost:5000/v2.0/',
               help="Dashboard Openstack url, v2"),
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


compute_group = cfg.OptGroup(name='compute',
                             title='Compute Service Options')

ComputeGroup = [
    cfg.BoolOpt('allow_tenant_isolation',
                default=True,
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
               default=160,
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
    cfg.ListOpt('compute_nodes',
                default=[],
                help="IP addresses of compute nodes"),
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
    cfg.StrOpt('neutron_cidr',
               default="10.100.0.0/16",
               help="The cidr block to allocate tenant networks from"),
    cfg.StrOpt('neutron_ext_cidr',
               default="10.100.0.0/16",
               help="The cidr block to allocate tenant networks from"),
    cfg.StrOpt('network_provider',
               default="nova_network",
               help="Value of network provider"),
    cfg.IntOpt('tenant_network_mask_bits',
               default=29,
               help="The mask bits for tenant networks"),
    cfg.BoolOpt('tenant_networks_reachable',
                default=False,
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

savanna = cfg.OptGroup(name='savanna',
                       title='Savanna Service Options')

SavannaConfig = [
    cfg.StrOpt('ip',
               default='10.20.0.131',
               help="IP of savanna service."),
    cfg.StrOpt('port',
               default=8386,
               help="Port of savanna service."),
    cfg.StrOpt('api_version',
               default='v1.0',
               help="API version of savanna service."),
    cfg.StrOpt('plugin',
               default='vanilla',
               help="Plugin name of savanna service."),
    cfg.StrOpt('pligin_version',
               default='1.1.2',
               help="Plugin version of savanna service."),
    cfg.StrOpt('tt_config',
               default={'Task Tracker Heap Size': 515},
               help="Task Tracker config  of savanna service."),
]


def register_savanna_opts(conf):
    conf.register_group(savanna)
    for opt in SavannaConfig:
        conf.register_opt(opt, group='savanna')


murano_group = cfg.OptGroup(name='murano',
                            title='Murano API Service Options')

MuranoConfig = [
    cfg.StrOpt('api_url',
               default=None,
               help="Murano API Service URL."),
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

def register_heat_opts(conf):
    conf.register_group(heat_group)
    for opt in HeatConfig:
        conf.register_opt(opt, group='heat')



def process_singleton(cls):
    """Wrapper for classes... To be instantiated only one time per process"""
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

            if not (os.path.isfile(path) or
                    'FUEL_CONFIG_DIR' in os.environ or
                    'FUEL_CONFIG' in os.environ):
                path = failsafe_path

        LOG.info("Using fuel config file %s" % path)

        if not os.path.exists(path):
            msg = "Config file %(path)s not found" % locals()
            print >> sys.stderr, RuntimeError(msg)
        else:
            config_files.append(path)

        cfg.CONF([], project='fuel', default_config_files=config_files)

        register_compute_opts(cfg.CONF)
        register_identity_opts(cfg.CONF)
        register_network_opts(cfg.CONF)
        register_volume_opts(cfg.CONF)
        register_murano_opts(cfg.CONF)
        register_heat_opts(cfg.CONF)
        self.compute = cfg.CONF.compute
        self.identity = cfg.CONF.identity
        self.network = cfg.CONF.network
        self.volume = cfg.CONF.volume
        self.murano = cfg.CONF.murano
        self.heat = cfg.CONF.heat


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
    network = ConfigGroup(NetworkGroup)
    volume = ConfigGroup(VolumeGroup)
    object_storage = ConfigGroup(ObjectStoreConfig)
    murano = ConfigGroup(MuranoConfig)
    heat = ConfigGroup(HeatConfig)

    def __init__(self, parse=True):
        LOG.info('INITIALIZING NAILGUN CONFIG')
        self.nailgun_host = os.environ.get('NAILGUN_HOST', None)
        self.nailgun_port = os.environ.get('NAILGUN_PORT', None)
        self.nailgun_url = 'http://{0}:{1}'.format(self.nailgun_host,
                                                   self.nailgun_port)
        self.cluster_id = os.environ.get('CLUSTER_ID', None)
        self.req_session = requests.Session()
        self.req_session.trust_env = False
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
            self._parse_murano_configuration()
            LOG.info('parse murano configuration successful')
            self._parse_heat_configuration()
            LOG.info('parse heat configuration successful')
            self._parse_cluster_generated_data()
            LOG.info('parse generated successful')
        except Exception, e:
            LOG.warning('Nailgun config creation failed. '
                        'Something wrong with endpoints')

    def _parse_murano_configuration(self):
        murano_url = self.network.raw_data.get('public_vip',
                                               self.compute.public_ips[0])
        self.murano.api_url = 'http://{0}:8082'.format(murano_url)

    def _parse_heat_configuration(self):
        endpoint = self.network.raw_data.get('public_vip',
                                             self.compute.public_ips[0])
        self.heat.endpoint = 'http://{0}:8004/v1'.format(endpoint)

    def _parse_cluster_attributes(self):
        api_url = '/api/clusters/%s/attributes' % self.cluster_id
        response = self.req_session.get(self.nailgun_url + api_url)
        LOG.info('RESPONSE %s STATUS %s' % (api_url, response.status_code))
        data = response.json()
        network_provider = data.get('net_provider', 'nova_network')
        LOG.info('RESPONSE FROM %s - %s' % (api_url, data))
        access_data = data['editable']['access']
        self.identity.admin_tenant_name = access_data['tenant']['value']
        self.identity.admin_username = access_data['user']['value']
        self.identity.admin_password = access_data['password']['value']
        self.network.network_provider = network_provider
        api_url = '/api/clusters/%s' % self.cluster_id
        cluster_data = self.req_session.get(self.nailgun_url + api_url).json()
        deployment_os = cluster_data['release']['operating_system']
        if deployment_os != 'RHEL':
            storage = data['editable']['storage']['volumes_ceph']
            self.volume.ceph_exist = storage

    def _parse_nodes_cluster_id(self):
        api_url = '/api/nodes?cluster_id=%s' % self.cluster_id
        response = self.req_session.get(self.nailgun_url + api_url)
        LOG.info('RESPONSE %s STATUS %s' % (api_url, response.status_code))
        data = response.json()
        controller_nodes = filter(lambda node: 'controller' in node['roles'],
                                  data)
        cinder_nodes = filter(lambda node: 'cinder' in node['roles'],
                              data)
        controller_ips = []
        conntroller_names = []
        public_ips = []
        for node in controller_nodes:
            public_network = next(network for network in node['network_data']
                                  if network['name'] == 'public')
            ip = public_network['ip'].split('/')[0]
            public_ips.append(ip)
            controller_ips.append(node['ip'])
            conntroller_names.append(node['fqdn'])
        LOG.info("IP %s NAMES %s" % (controller_ips, conntroller_names))
        self.compute.public_ips = public_ips
        self.compute.controller_nodes = controller_ips
        if not cinder_nodes:
            self.volume.cinder_node_exist = False

        compute_nodes = filter(lambda node: 'compute' in node['roles'],
                               data)
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
        self.compute.deployment_os = data['release']['operating_system']

    def _parse_networks_configuration(self):
        api_url = '/api/clusters/{0}/network_configuration/{1}'.format(
            self.cluster_id, self.network.network_provider)
        data = self.req_session.get(self.nailgun_url + api_url).json()
        self.network.raw_data = data
        if self.network.network_provider == 'neutron':
            neutron_data = data['networks']['predefined_networks']
            self.network.neutron_cidr= neutron_data['net04']['L3']['cidr']
            self.network.neutron_ext_cidr = neutron_data['net04_ext']['L3']['cidr']

    def _parse_cluster_generated_data(self):
        api_url = '/api/clusters/%s/generated' % self.cluster_id
        data = self.req_session.get(self.nailgun_url + api_url).json()
        self.generated_data = data
        if 'RHEL' not in self.compute.deployment_os:
            amqp_data = data['rabbit']
            self.amqp_pwd = amqp_data['password']
        else:
            amqp_data = data['qpid']
            self.amqp_pwd = amqp_data['password']
            storage = data['storage']['volumes_ceph']
            self.volume.ceph_exist = storage

    def _parse_ostf_api(self):
        """
            will leave this
        """
        api_url = '/api/ostf/%s' % self.cluster_id
        response = self.req_session.get(self.nailgun_url + api_url)
        data = response.json()
        self.identity.url = data['horizon_url'] + 'dashboard'
        self.identity.uri = data['keystone_url'] + 'v2.0/'

    def set_proxy(self):
        """Sets environment property for http_proxy:
            To behave properly - method must be called after all nailgun params
            is processed
        """
        os.environ['http_proxy'] = 'http://{0}:{1}'.format(
            self.compute.controller_nodes[0], 8888)

    def set_endpoints(self):
        public_vip = self.network.raw_data.get('public_vip', None)
        # workaround for api without public_vip for ha mode
        if not public_vip and 'ha' in self.mode:
            self._parse_ostf_api()
        else:
            endpoint = public_vip or self.compute.public_ips[0]
            self.identity.url = 'http://{0}/{1}/'.format(endpoint, 'dashboard')
            self.identity.ubuntu_url = 'http://{0}/'.format(endpoint)
            self.identity.uri = 'http://{0}:{1}/{2}/'.format(
                endpoint, 5000, 'v2.0')


def FuelConfig():
    if 'CUSTOM_FUEL_CONFIG' in os.environ:
        return FileConfig()
    else:
        return NailgunConfig()
