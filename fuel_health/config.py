# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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
               default=None,
               help="Full URI of the OpenStack Identity API (Keystone), v2"),
    cfg.StrOpt('url',
               default='http://10.0.0.1/',
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
               default='admin',
               help="Administrative Username to use for"
                    "Keystone API requests."),
    cfg.StrOpt('admin_tenant_name',
               default='admin',
               help="Administrative Tenant name to use for Keystone API "
                    "requests."),
    cfg.StrOpt('admin_password',
               default='admin',
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
               default=300,
               help="Timeout in seconds to wait for an instance to build."),
    cfg.BoolOpt('run_ssh',
                default=False,
                help="Does the test environment support snapshots?"),
    cfg.StrOpt('ssh_user',
               default='root',
               help="User name used to authenticate to an instance."),
    cfg.IntOpt('ssh_timeout',
               default=300,
               help="Timeout in seconds to wait for authentication to "
                    "succeed."),
    cfg.IntOpt('ssh_channel_timeout',
               default=60,
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
    cfg.ListOpt('enabled_services',
                default=[],
                help="If false, skip config tests regardless of the "
                     "extension status"),
    cfg.ListOpt('controller_nodes',
                default=[],
                help="IP address of one of the controller nodes"),
    cfg.ListOpt('controller_nodes_name',
                default=[],
                help="DNS name of one of the controller nodes"),
    cfg.StrOpt('controller_node_ssh_user',
               default='ssh_user',
               help="ssh user of one of the controller nodes"),
    cfg.StrOpt('controller_node_ssh_password',
               default='pass',
               help="ssh user pass of one of the controller nodes"),
    cfg.StrOpt('controller_node_ssh_key_path',
               default='/root/.ssh/id_rsa',
               help="path to ssh key"),
    cfg.StrOpt('image_name',
               default="cirros",
               help="Valid secondary image reference to be used in tests."),
    cfg.IntOpt('flavor_ref',
               default=1,
               help="Valid primary flavor to use in tests.")

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
               help='Catalog type of the Quantum service.'),
    cfg.StrOpt('tenant_network_cidr',
               default="10.100.0.0/16",
               help="The cidr block to allocate tenant networks from"),
    cfg.IntOpt('tenant_network_mask_bits',
               default=29,
               help="The mask bits for tenant networks"),
    cfg.BoolOpt('tenant_networks_reachable',
                default=True,
                help="Whether tenant network connectivity should be "
                     "evaluated directly"),
    cfg.BoolOpt('quantum_available',
                default=False,
                help="Whether or not quantum is expected to be available"),
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
               default=300,
               help='Timeout in seconds to wait for a volume to become'
                    'available.'),
    cfg.StrOpt('catalog_type',
               default='volume',
               help="Catalog type of the Volume Service"),
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


def process_singleton(cls):
    """Wrapper for classes... To be instantiated only one time per process"""
    instances = {}

    def wrapper(*args, **kwargs):
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
        self.compute = cfg.CONF.compute
        self.identity = cfg.CONF.identity
        self.network = cfg.CONF.network
        self.volume = cfg.CONF.volume
        os.environ['http_proxy'] = 'http://{0}:{1}'.format(
            self.compute.controller_nodes[0], 8888)


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

    def __init__(self, parse=True):
        LOG.info('INITIALIZING NAILGUN CONFIG')
        self.nailgun_host = os.environ.get('NAILGUN_HOST', None)
        self.nailgun_port = os.environ.get('NAILGUN_PORT', None)
        self.nailgun_url = 'http://{0}:{1}'.format(self.nailgun_host,
                                                   self.nailgun_port)
        self.cluster_id = os.environ.get('CLUSTER_ID', None)
        if parse:
            self.prepare_config()

    def prepare_config(self, *args, **kwargs):
        for interface in dir(self):
            if interface.startswith('_parse'):
                method = getattr(self, interface)
                if callable(method):
                    method()

    def _parse_ostf(self):
        """
        RESPONSE FORMAT
        {
            "controller_nodes_ips": [
                "10.20.0.129"
            ],
            "horizon_url": "http://240.0.1.2/",
            "controller_nodes_names": [
                "controller-1.example.com"
            ],
            "keystone_url": "http://240.0.1.2:5000/",
            "admin_tenant_name": "admin",
            "admin_username": "admin",
            "admin_password": "admin"
        }
        """
        api_url = '/api/ostf/%s' % self.cluster_id
        response = requests.get(self.nailgun_url+api_url)
        if response.status_code == 404:
            LOG.warning('URL %s is not implemented '
                        'in nailgun api' % api_url)
        elif response.status_code == 200:
            data = response.json()
            self.identity.url = data['horizon_url'] + 'dashboard'
            self.identity.uri = data['keystone_url'] + 'v2.0/'
            self.identity.admin_tenant_name = data['admin_tenant_name']
            self.identity.admin_username = data['admin_username']
            self.identity.admin_password = data['admin_password']
            self.compute.controller_nodes = data['controller_nodes_ips']
            self.compute.controller_nodes_name = \
                data['controller_nodes_names']
            os.environ['http_proxy'] = 'http://{0}:{1}'.format(
                self.compute.controller_nodes[0], 8888)

    def _parse_networks_configuration(self):
        """
        {
    "net_manager": "FlatDHCPManager",
    "networks": [
        {
            "network_size": 256,
            "name": "floating",
            "ip_ranges": [
                [
                    "172.18.8.42",
                    "172.18.8.47"
                ]
            ],
            "amount": 1,
            "id": 27,
            "netmask": "255.255.255.0",
            "cluster_id": 6,
            "vlan_start": 522,
            "cidr": "240.0.0.0/24",
            "gateway": "240.0.0.1"
        },
        {
            "network_size": 256,
            "name": "management",
            "ip_ranges": [
                [
                    "192.168.0.2",
                    "192.168.0.254"
                ]
            ],
            "amount": 1,
            "id": 29,
            "netmask": "255.255.255.0",
            "cluster_id": 6,
            "vlan_start": 101,
            "cidr": "192.168.0.0/24",
            "gateway": "192.168.0.1"
        },
        {
            "network_size": 256,
            "name": "storage",
            "ip_ranges": [
                [
                    "172.16.0.2",
                    "172.16.0.254"
                ]
            ],
            "amount": 1,
            "id": 30,
            "netmask": "255.255.255.0",
            "cluster_id": 6,
            "vlan_start": 102,
            "cidr": "172.16.0.0/24",
            "gateway": "172.16.0.1"
        },
        {
            "network_size": 256,
            "name": "fixed",
            "ip_ranges": [
                [
                    "10.0.0.2",
                    "10.0.0.254"
                ]
            ],
            "amount": 1,
            "id": 31,
            "netmask": "255.255.255.0",
            "cluster_id": 6,
            "vlan_start": 103,
            "cidr": "10.0.0.0/24",
            "gateway": "10.0.0.1"
        },
        {
            "network_size": 256,
            "name": "public",
            "ip_ranges": [
                [
                    "172.18.8.50",
                    "172.18.8.59"
                ]
            ],
            "amount": 1,
            "id": 28,
            "netmask": "255.255.255.224",
            "cluster_id": 6,
            "vlan_start": 522,
            "cidr": "240.0.1.0/24",
            "gateway": "172.18.8.33"
        }
    ]
}
        """
        api_url = '/api/clusters/%s/network_configuration/' % self.cluster_id
        data = requests.get(self.nailgun_url+api_url).json()
        self.network.raw_data = data


def FuelConfig():
    if all(item in os.environ for item in
           ('NAILGUN_HOST', 'NAILGUN_PORT', 'CLUSTER_ID')):
        return NailgunConfig()
    return FileConfig()
