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

import logging
import netaddr
import time

LOG = logging.getLogger(__name__)

# Default client libs
try:
    import heatclient.v1.client
except:
    LOG.warning('Heatclient could not be imported.')
try:
    import muranoclient.v1.client
except:
    LOG.warning('Muranoclient could not be imported.')
try:
    import savannaclient.api.client
except:
    LOG.warning('Savanna client could not be imported.')

try:
    import neutronclient.v2_0.client
except:
    LOG.warning('Savanna client could not be imported.')
import cinderclient.client
import glanceclient.client
import keystoneclient.v2_0.client
import novaclient.client

from fuel_health.common.ssh import Client as SSHClient
from fuel_health.exceptions import SSHExecCommandFailed
from fuel_health.common.utils.data_utils import rand_name
from fuel_health.common.utils.data_utils import rand_int_id
from fuel_health import exceptions
import fuel_health.manager
import fuel_health.test
from fuel_health import config


class OfficialClientManager(fuel_health.manager.Manager):
    """
    Manager that provides access to the official python clients for
    calling various OpenStack APIs.
    """

    NOVACLIENT_VERSION = '2'
    CINDERCLIENT_VERSION = '1'

    def __init__(self):
        super(OfficialClientManager, self).__init__()
        self.compute_client = self._get_compute_client()
        self.image_client = self._get_image_client()
        self.identity_client = self._get_identity_client()
        self.network_client = self._get_network_client()
        self.volume_client = self._get_volume_client()
        self.heat_client = self._get_heat_client()
        self.murano_client = self._get_murano_client()
        self.savanna_client = self._get_savanna_client()

        self.client_attr_names = [
            'compute_client',
            'image_client',
            'identity_client',
            'network_client',
            'volume_client',
            'heat_client',
            'murano_client',
            'savanna_client'
        ]

    def _get_compute_client(self, username=None, password=None,
                            tenant_name=None):
        if not username:
            username = self.config.identity.admin_username
        if not password:
            password = self.config.identity.admin_password
        if not tenant_name:
            tenant_name = self.config.identity.admin_tenant_name

        if None in (username, password, tenant_name):
            msg = ("Missing required credentials for compute client. "
                   "username: %(username)s, password: %(password)s, "
                   "tenant_name: %(tenant_name)s") % locals()
            raise exceptions.InvalidConfiguration(msg)

        auth_url = self.config.identity.uri
        dscv = self.config.identity.disable_ssl_certificate_validation

        client_args = (username, password, tenant_name, auth_url)

        # Create our default Nova client to use in testing
        service_type = self.config.compute.catalog_type
        return novaclient.client.Client(self.NOVACLIENT_VERSION,
                                        *client_args,
                                        service_type=service_type,
                                        no_cache=True,
                                        insecure=dscv)

    def _get_image_client(self):
        keystone = self._get_identity_client()
        token = keystone.auth_token
        endpoint = keystone.service_catalog.url_for(service_type='image',
                                                    endpoint_type='publicURL')
        dscv = self.config.identity.disable_ssl_certificate_validation
        return glanceclient.Client('1', endpoint=endpoint, token=token,
                                   insecure=dscv)

    def _get_volume_client(self, username=None, password=None,
                           tenant_name=None):
        if not username:
            username = self.config.identity.admin_username
        if not password:
            password = self.config.identity.admin_password
        if not tenant_name:
            tenant_name = self.config.identity.admin_tenant_name

        auth_url = self.config.identity.uri
        return cinderclient.client.Client(self.CINDERCLIENT_VERSION,
                                          username,
                                          password,
                                          tenant_name,
                                          auth_url)

    def _get_identity_client(self, username=None, password=None,
                             tenant_name=None):
        if not username:
            username = self.config.identity.admin_username
        if not password:
            password = self.config.identity.admin_password
        if not tenant_name:
            tenant_name = self.config.identity.admin_tenant_name

        if None in (username, password, tenant_name):
            msg = ("Missing required credentials for identity client. "
                   "username: %(username)s, password: %(password)s, "
                   "tenant_name: %(tenant_name)s") % locals()
            raise exceptions.InvalidConfiguration(msg)

        auth_url = self.config.identity.uri
        dscv = self.config.identity.disable_ssl_certificate_validation

        return keystoneclient.v2_0.client.Client(username=username,
                                                 password=password,
                                                 tenant_name=tenant_name,
                                                 auth_url=auth_url,
                                                 insecure=dscv)

    def _get_network_client(self):
        username = self.config.identity.admin_username
        password = self.config.identity.admin_password
        tenant_name = self.config.identity.admin_tenant_name

        auth_url = self.config.identity.uri
        dscv = self.config.identity.disable_ssl_certificate_validation



        return neutronclient.v2_0.client.Client(username=username,
                                    tenant_name=tenant_name,
                                    password=password,
                                    auth_url=auth_url)

    def _get_heat_client(self, username=None, password=None):
        keystone = self._get_identity_client()
        token = keystone.auth_token
        auth_url = self.config.identity.uri

        endpoint = self.config.heat.endpoint
        if not username:
            username = self.config.identity.admin_username
        if not password:
            password = self.config.identity.admin_password

        return heatclient.v1.client.Client(endpoint,
                                           auth_url=auth_url, token=token,
                                           username=username,
                                           password=password)

    def _get_murano_client(self):
        """
        This method returns Murano API client
        """
        # Get xAuth token from Keystone
        self.token_id = self._get_identity_client(
            self.config.identity.admin_username,
            self.config.identity.admin_password,
            self.config.identity.admin_tenant_name).auth_token

        # Get Murano API parameters
        self.api_host = None
        self.insecure = False
        if hasattr(self.config.murano, 'api_url'):
            self.api_host = self.config.murano.api_url
        if hasattr(self.config.murano, 'insecure'):
            self.insecure = self.config.murano.insecure

        return muranoclient.v1.client.Client(endpoint=self.api_host,
                                             token=self.token_id,
                                             insecure=self.insecure)

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


class OfficialClientTest(fuel_health.test.TestCase):
    manager_class = OfficialClientManager

    @classmethod
    def _create_nano_flavor(cls):
        name = rand_name('ost1_test-flavor-nano')
        flavorid = 42
        flavor_list = cls.compute_client.flavors.list()
        if flavor_list:
            for flavor in flavor_list:
                LOG.debug(flavor.id)
                if '42' in flavor.id:
                    LOG.info('42 flavor id already exists')
                    return flavor

            flavor = cls.compute_client.flavors.create(
                name, 64, 1, 1, flavorid)
            return flavor

    @classmethod
    def tearDownClass(cls):
        cls.error_msg = []
        try:
            cls.compute_client.flavors.delete('42')
        except Exception as exc:
            cls.error_msg.append(exc)
            LOG.debug(exc)
            pass
        while cls.os_resources:
            thing = cls.os_resources.pop()
            LOG.debug("Deleting %r from shared resources of %s" %
                      (thing, cls.__name__))

            try:
                # OpenStack resources are assumed to have a delete()
                # method which destroys the resource...
                thing.delete()
            except Exception as e:
                # If the resource is already missing, mission accomplished.
                if e.__class__.__name__ == 'NotFound':
                    continue
                cls.error_msg.append(e)
                LOG.debug(e)

            def is_deletion_complete():
                # Deletion testing is only required for objects whose
                # existence cannot be checked via retrieval.
                if isinstance(thing, dict):
                    return True
                try:
                    thing.get()
                except Exception as e:
                    # Clients are expected to return an exception
                    # called 'NotFound' if retrieval fails.
                    if e.__class__.__name__ == 'NotFound':
                        return True
                    cls.error_msg.append(e)
                    LOG.debug(e)
                return False

            # Block until resource deletion has completed or timed-out
            fuel_health.test.call_until_true(is_deletion_complete, 10, 1)


class NetworkScenarioTest(OfficialClientTest):
    """
    Base class for nova network scenario tests
    """

    @classmethod
    def setUpClass(cls):
        super(NetworkScenarioTest, cls).setUpClass()
        cls.host = cls.config.compute.controller_nodes
        cls.usr = cls.config.compute.controller_node_ssh_user
        cls.pwd = cls.config.compute.controller_node_ssh_password
        cls.key = cls.config.compute.path_to_private_key
        cls.timeout = cls.config.compute.ssh_timeout
        cls.tenant_id = cls.manager._get_identity_client(
            cls.config.identity.admin_username,
            cls.config.identity.admin_password,
            cls.config.identity.admin_tenant_name).tenant_id
        cls.network = []
        cls.floating_ips = []
        cls.sec_group = []
        cls.error_msg = []

    def _create_keypair(self, client, namestart='ost1_test-keypair-smoke-'):
        kp_name = rand_name(namestart)
        keypair = client.keypairs.create(kp_name)
        self.set_resource(kp_name, keypair)
        self.verify_response_body_content(keypair.id,
                                          kp_name,
                                          'Keypair creation failed')
        return keypair

    def _create_security_group(
            self, client, namestart='ost1_test-secgroup-smoke-netw'):
        # Create security group
        sg_name = rand_name(namestart)
        sg_desc = sg_name + " description"
        secgroup = client.security_groups.create(sg_name, sg_desc)
        self.set_resource(sg_name, secgroup)
        self.verify_response_body_content(secgroup.name,
                                          sg_name,
                                          "Security group creation failed")
        self.verify_response_body_content(secgroup.description,
                                          sg_desc,
                                          "Security group creation failed")

        # Add rules to the security group

        # These rules are intended to permit inbound ssh and icmp
        # traffic from all sources, so no group_id is provided.
        # Setting a group_id would only permit traffic from ports
        # belonging to the same security group.
        rulesets = [
            {
                # ssh
                'ip_protocol': 'tcp',
                'from_port': 22,
                'to_port': 22,
                'cidr': '0.0.0.0/0',
            },
            {
                # ping
                'ip_protocol': 'icmp',
                'from_port': -1,
                'to_port': -1,
                'cidr': '0.0.0.0/0',
            }
        ]
        for ruleset in rulesets:
            try:
                client.security_group_rules.create(secgroup.id, **ruleset)
            except Exception:
                self.fail("Failed to create rule in security group.")

        return secgroup

    def _create_network(self, label='ost1_test-network-smoke-'):
        n_label = rand_name(label)
        cidr = self.config.network.tenant_network_cidr
        networks = self.compute_client.networks.create(
            label=n_label, cidr=cidr)
        self.set_resource(n_label, networks)
        self.network.append(networks)
        self.verify_response_body_content(networks.label,
                                          n_label,
                                          "Network creation failed")
        return networks

    def _list_networks_neutron(self):
        nets = self.network_client.list_networks()
        return nets['networks']

    def _list_subnets_neutron(self):
        subnets = self.network_client.list_subnets()
        return subnets['subnets']

    def _list_routers_neutron(self):
        routers = self.network_client.list_routers()
        return routers['routers']

    def _create_router(self, tenant_id, namestart='ost1_test-create_router-neutron'):
        name = rand_name(namestart)
        body = dict(
            router=dict(
                name=name,
                admin_state_up=True,
                tenant_id=tenant_id,
            ),
        )
        result = self.network_client.create_router(body=body)
        router = result['router']
        self.assertEqual(router.name, name)
        self.set_resource(name, router)
        return router

    def _add_interface_to_router(self, router, subnet_id):
        self.network_client.add_interface_router(router,
                                                 {'subnet_id': subnet_id})

    def _create_network_neutron(self, tenant_id,
                                namestart='ost1_test-create_net-neutron'):
        name = rand_name(namestart)
        body = dict(
            network=dict(
                name=name,
                tenant_id=tenant_id,
            ),
        )
        result = self.network_client.create_network(body=body)
        return result

    def _create_subnet(self, network, namestart='ost1_test-subnet-'):
        cfg = self.config.network
        tenant_cidr = netaddr.IPNetwork(cfg.tenant_network_cidr)
        result = None
        # Repeatedly attempt subnet creation with sequential cidr
        # blocks until an unallocated block is found.
        for subnet_cidr in tenant_cidr.subnet(cfg.tenant_network_mask_bits):
            body = dict(
                subnet=dict(
                    ip_version=4,
                    network_id=network.id,
                    tenant_id=network.tenant_id,
                    cidr=str(subnet_cidr),
                ),
            )
            try:
                result = self.network_client.create_subnet(body=body)
                break
            except exc.NeutronClientException as e:
                is_overlapping_cidr = 'overlaps with another subnet' in str(e)
                if not is_overlapping_cidr:
                    raise
        self.assertIsNotNone(result, 'Unable to allocate tenant network')
        subnet = net_common.DeletableSubnet(client=self.network_client,
                                            **result['subnet'])
        self.assertEqual(subnet.cidr, str(subnet_cidr))
        self.set_resource(rand_name(namestart), subnet)
        return subnet


    @classmethod
    def _clear_networks(cls):
        try:
            for net in cls.network:
                cls.compute_client.networks.delete(net)
        except Exception as exc:
            cls.error_msg.append(exc)
            LOG.debug(exc)
            pass

    def _list_networks(self):
        nets = self.compute_client.networks.list()
        return nets

    def _create_server(self, client, name, security_groups):
        base_image_id = get_image_from_name()
        create_kwargs = {
            'security_groups': security_groups,
        }
        self._create_nano_flavor()
        server = client.servers.create(name, base_image_id, 42,
                                       **create_kwargs)
        self.verify_response_body_content(server.name,
                                          name,
                                          "Instance creation failed")
        self.set_resource(name, server)
        self.status_timeout(client.servers, server.id, 'ACTIVE')
        # The instance retrieved on creation is missing network
        # details, necessitating retrieval after it becomes active to
        # ensure correct details.
        server = client.servers.get(server.id)
        self.set_resource(name, server)
        return server

    def _create_floating_ip(self):
        floating_ips_pool = self.compute_client.floating_ip_pools.list()

        if floating_ips_pool:
            floating_ip = self.compute_client.floating_ips.create(
                pool=floating_ips_pool[0].name)

            self.floating_ips.append(floating_ip)
            return floating_ip
        else:
            self.fail('No available floating IP found')

    def _assign_floating_ip_to_instance(self, client, server, floating_ip):
        try:
            client.servers.add_floating_ip(server, floating_ip)
        except Exception:
            self.fail('Can not assign floating ip to instance')

    @classmethod
    def _clean_floating_is(cls):
        for ip in cls.floating_ips:
            try:
                cls.compute_client.floating_ips.delete(ip)
            except Exception as exc:
                cls.error_msg.append(exc)
                LOG.debug(exc)
                pass

    def _ping_ip_address(self, ip_address):
        def ping():
            cmd = 'ping -c1 -w1 ' + ip_address
            time.sleep(30)

            if self.host:

                try:
                    SSHClient(self.host[0],
                              self.usr, self.pwd,
                              key_filename=self.key,
                              timeout=self.timeout).exec_command(cmd)
                    return True

                except SSHExecCommandFailed as exc:
                    output_msg = "Instance is not reachable by floating IP."
                    LOG.debug(exc)
                    self.fail(output_msg)
                except Exception as exc:
                    LOG.debug(exc)
                    self.fail("Connection failed.")

            else:
                self.fail('Wrong tests configurations, one from the next '
                          'parameters are empty controller_node_name or '
                          'controller_node_ip ')

        # TODO Allow configuration of execution and sleep duration.
        return fuel_health.test.call_until_true(ping, 40, 1)

    def _ping_ip_address_from_instance(self, ip_address, viaHost=None):
        def ping():
            time.sleep(30)
            ssh_timeout = self.timeout > 30 and self.timeout or 30
            if not (self.host or viaHost):
                self.fail('Wrong tests configurations, one from the next '
                          'parameters are empty controller_node_name or '
                          'controller_node_ip ')
            try:
                host = viaHost or self.host[0]
                ssh = SSHClient(host,
                                self.usr, self.pwd,
                                key_filename=self.key,
                                timeout=ssh_timeout)
                LOG.debug('Get ssh to auxiliary host')
                ssh.exec_command_on_vm(command='ping -c1 -w1 8.8.8.8',
                                       user='cirros',
                                       password='cubswin:)',
                                       vm=ip_address)
                LOG.debug('Get ssh to instance')
                return True
            except SSHExecCommandFailed as exc:
                output_msg = "Ping command failed."
                LOG.debug(exc)
                self.fail(output_msg)
            except Exception as exc:
                LOG.debug(exc)
                self.fail("Connection failed.")

        # TODO Allow configuration of execution and sleep duration.
        return fuel_health.test.call_until_true(ping, 40, 1)

    def _check_vm_connectivity(self, ip_address):
        self.assertTrue(self._ping_ip_address(ip_address),
                        "Timed out waiting for %s to become "
                        "reachable. Please, check Network "
                        "configuration" % ip_address)

    def _check_connectivity_from_vm(self, ip_address, viaHost=None):
        self.assertTrue(self._ping_ip_address_from_instance(ip_address,
                                                            viaHost=viaHost),
                        "Timed out waiting for %s to become "
                        "reachable. Please, check Network "
                        "configuration" % ip_address)

    @classmethod
    def _verification_of_exceptions(cls):
        if cls.error_msg:
            for err in cls.error_msg:
                if err.__class__.__name__ == 'InternalServerError':
                    raise cls.failureException('REST API of '
                                               'OpenStack is inaccessible.'
                                               ' Please try again')
                if err.__class__.__name__ == 'ClientException':
                    raise cls.failureException('REST API of '
                                               'OpenStack is inaccessible.'
                                               ' Please try again')

    @classmethod
    def tearDownClass(cls):
        super(NetworkScenarioTest, cls).tearDownClass()
        cls._clean_floating_is()
        cls._clear_networks()
        cls._verification_of_exceptions()


def get_image_from_name():
    cfg = config.FuelConfig()
    image_name = cfg.compute.image_name
    image_client = OfficialClientManager()._get_compute_client()
    images = image_client.images.list()
    LOG.debug(images)
    if images:
        for im in images:
            LOG.debug(im.name)
            if im.name.strip().lower() == image_name.strip().lower():
                return im.id
    else:
        raise exceptions.ImageFault


class SanityChecksTest(OfficialClientTest):
    """
    Base class for openstack sanity tests
    """

    _enabled = True

    @classmethod
    def check_preconditions(cls):
        cls._enabled = True
        if cls.config.network.neutron_available:
            cls._enabled = False
        else:
            cls._enabled = True
            # ensure the config says true
            try:
                cls.compute_client.networks.list()
            except exceptions.EndpointNotFound:
                cls._enabled = False

    def setUp(self):
        super(SanityChecksTest, self).setUp()
        if not self._enabled:
            self.fail('Nova Networking is not available')

    @classmethod
    def setUpClass(cls):
        super(SanityChecksTest, cls).setUpClass()
        cls.tenant_id = cls.manager._get_identity_client(
            cls.config.identity.admin_username,
            cls.config.identity.admin_password,
            cls.config.identity.admin_tenant_name).tenant_id
        cls.network = []
        cls.floating_ips = []

    @classmethod
    def tearDownClass(cls):
        pass

    def _list_instances(self, client):
        instances = client.servers.list()
        return instances

    def _list_images(self, client):
        images = client.images.list()
        return images

    def _list_volumes(self, client):
        volumes = client.volumes.list(detailed=False)
        return volumes

    def _list_snapshots(self, client):
        snapshots = client.volume_snapshots.list(detailed=False)
        return snapshots

    def _list_flavors(self, client):
        flavors = client.flavors.list()
        return flavors

    def _list_limits(self, client):
        limits = client.limits.get()
        return limits

    def _list_services(self, client):
        services = client.services.list()
        return services

    def _list_users(self, client):
        users = client.users.list()
        return users

    def _list_networks(self, client):
        networks = client.networks.list()
        return networks


class SmokeChecksTest(OfficialClientTest):
    """
    Base class for openstack smoke tests
    """

    _enabled = True

    def setUp(self):
        super(SmokeChecksTest, self).setUp()
        if not self._enabled:
            self.fail('Nova Networking is not available')

    @classmethod
    def setUpClass(cls):
        super(SmokeChecksTest, cls).setUpClass()
        cls._create_nano_flavor()
        cls.tenant_id = cls.manager._get_identity_client(
            cls.config.identity.admin_username,
            cls.config.identity.admin_password,
            cls.config.identity.admin_tenant_name).tenant_id
        cls.build_interval = cls.config.volume.build_interval
        cls.build_timeout = cls.config.volume.build_timeout

        cls.flavors = []
        cls.tenants = []
        cls.users = []
        cls.roles = []
        cls.volumes = []
        cls.error_msg = []

    def _create_flavors(self, client, ram, disk, vcpus=1):
        name = rand_name('ost1_test-flavor-')
        flavorid = rand_int_id()
        flavor = client.flavors.create(name, ram, disk, vcpus, flavorid)
        self.flavors.append(flavor)
        return flavor

    @classmethod
    def _clean_flavors(cls):
        if cls.flavors:
            for flav in cls.flavors:
                try:
                    cls.compute_client.flavors.delete(flav)
                except Exception as exc:
                    cls.error_msg.append(exc)
                    LOG.debug(exc)
                    pass

    def _create_tenant(self, client):
        name = rand_name('ost1_test-tenant-')
        tenant = client.tenants.create(name)
        self.tenants.append(tenant)
        return tenant

    @classmethod
    def _clean_tenants(cls):
        if cls.tenants:
            for ten in cls.tenants:
                try:
                    cls.identity_client.tenants.delete(ten)
                except Exception as exc:
                    cls.error_msg.append(exc)
                    LOG.debug(exc)
                    pass

    def _create_user(self, client, tenant_id):
        password = "123456"
        email = "test@test.com"
        name = rand_name('ost1_test-user-')
        user = client.users.create(name, password, email, tenant_id)
        self.users.append(user)
        return user

    @classmethod
    def _clean_users(cls):
        if cls.users:
            for user in cls.users:
                try:
                    cls.identity_client.users.delete(user)
                except Exception as exc:
                    cls.error_msg.append(exc)
                    LOG.debug(exc)
                    pass

    def _create_role(self, client):
        name = rand_name('ost1_test-role-')
        role = client.roles.create(name)
        self.roles.append(role)
        return role

    @classmethod
    def _clean_roles(cls):
        if cls.roles:
            for role in cls.roles:
                try:
                    cls.identity_client.roles.delete(role)
                except Exception as exc:
                    cls.error_msg.append(exc)
                    LOG.debug(exc)
                    pass

    def _create_volume(self, client):
        display_name = rand_name('ost1_test-volume')
        volume = client.volumes.create(size=1, display_name=display_name)
        self.set_resource(display_name, volume)
        self.volumes.append(volume)
        return volume

    @classmethod
    def _clean_volumes(cls):
        if cls.volumes:
            for v in cls.volumes:
                if v.status == 'available' or v.status == 'error':
                    try:
                        cls.volume_client.volumes.delete(v)
                    except Exception as exc:
                        cls.error_msg.append(exc)
                        LOG.debug(exc)
                        pass
                else:
                    pass

    def _create_server(self, client):
        name = rand_name('ost1_test-volume-instance')
        base_image_id = get_image_from_name()
        flavor_id = self._create_nano_flavor().id
        server = client.servers.create(name, base_image_id, flavor_id)
        self.set_resource(name, server)
        self.verify_response_body_content(server.name,
                                          name,
                                          "Instance creation failed")
        # The instance retrieved on creation is missing network
        # details, necessitating retrieval after it becomes active to
        # ensure correct details.
        server = self._wait_server_param(client, server, 'addresses', 5, 1)
        #self.set_resource(name, server)
        return server

    def _wait_server_param(self, client, server, param_name,
                           tries=1, timeout=1, expected_value=None):
        while tries:
            val = getattr(server, param_name, None)
            if val:
                if (not expected_value) or (expected_value == val):
                    return server
            time.sleep(timeout)
            server = client.servers.get(server.id)
            tries -= 1
        return server

    def _attach_volume_to_instance(self, volume, instance):
        device = '/dev/vdb'
        attached_volume = self.compute_client.volumes.create_server_volume(
            volume_id=volume.id, server_id=instance, device=device)
        return attached_volume

    def _detach_volume(self, client, volume):
        volume = client.volumes.detach(volume)
        return volume

    def is_resource_deleted(self, volume):
        try:
            self.client.volumes.get(volume)
        except exceptions.NotFound:
            return True
        return False

    @classmethod
    def _verification_of_exceptions(cls):
        if cls.error_msg:
            for err in cls.error_msg:
                if err.__class__.__name__ == 'InternalServerError':
                    raise cls.failureException('REST API of '
                                               'OpenStack is inaccessible.'
                                               ' Please try again')
                if err.__class__.__name__ == 'ClientException':
                    raise cls.failureException('REST API of '
                                               'OpenStack is inaccessible.'
                                               ' Please try again')

    @classmethod
    def tearDownClass(cls):
        super(SmokeChecksTest, cls).tearDownClass()
        cls._clean_flavors()
        cls._clean_tenants()
        cls._clean_users()
        cls._clean_roles()
        cls._clean_volumes()
        cls._verification_of_exceptions()
