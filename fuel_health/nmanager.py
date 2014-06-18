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
import time
import traceback

LOG = logging.getLogger(__name__)

# Default client libs
try:
    import heatclient.v1.client
except:
    LOG.warning('Heatclient could not be imported.')
try:
    import muranoclient.v1.client
except:
    LOG.debug(traceback.format_exc())
    LOG.warning('Muranoclient could not be imported.')
try:
    import saharaclient.client
except:
    LOG.debug(traceback.format_exc())
    LOG.warning('Savanna client could not be imported.')
try:
    import ceilometerclient.v2.client
except:
    LOG.warning('Ceilometer client could not be imported.')

import cinderclient.client
import keystoneclient.v2_0.client
import novaclient.client

from fuel_health.common.ssh import Client as SSHClient
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
        self.clients_initialized = False
        self.traceback = ''
        self.keystone_error_message = None
        self.compute_client = self._get_compute_client()
        try:
            self.identity_client = self._get_identity_client()
            self.clients_initialized = True
        except Exception as e:
            if e.__class__.__name__ == 'Unauthorized':
                self.keystone_error_message = ('Unable to run test: OpenStack'
                                               ' Authorization Failure. '
                                               'If login or '
                                               'password was changed, '
                                               'please update '
                                               'environment settings. '
                                               'Please refer to Mirantis '
                                               'OpenStack documentation '
                                               'for more details.')
            LOG.debug(traceback.format_exc())
            self.traceback = traceback.format_exc()

        if self.clients_initialized:
            self.volume_client = self._get_volume_client()
            self.heat_client = self._get_heat_client()
            self.murano_client = self._get_murano_client()
            self.savanna_client = self._get_savanna_client()
            self.ceilometer_client = self._get_ceilometer_client()
            self.client_attr_names = [
                'compute_client',
                'identity_client',
                'volume_client',
                'heat_client',
                'murano_client',
                'savanna_client',
                'ceilometer_client'
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

    def _get_heat_client(self, username=None, password=None,
                         tenant_name=None):
        if not username:
            username = self.config.identity.admin_username
        if not password:
            password = self.config.identity.admin_password
        if not tenant_name:
            tenant_name = self.config.identity.admin_tenant_name

        keystone = self._get_identity_client(username, password, tenant_name)
        token = keystone.auth_token
        try:
            endpoint = self.config.heat.endpoint + "/" + keystone.tenant_id
        except keystoneclient.exceptions.EndpointNotFound:
            LOG.warning('Can not initialize heat client, endpoint not found')
            return None
        else:
            return heatclient.v1.client.Client(endpoint,
                                               token=token,
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

        try:
            return muranoclient.v1.client.Client(
                endpoint=self.config.murano.api_url,
                token=self.token_id,
                insecure=self.config.murano.insecure)
        except exceptions:
            LOG.debug(traceback.format_exc())
            LOG.warning('Can not initialize murano client')

    def _get_savanna_client(self, username=None, password=None):
        auth_url = self.config.identity.uri
        tenant_name = self.config.identity.admin_tenant_name
        savanna_url = self.config.savanna.api_url
        LOG.debug('Sahara url is %s' % savanna_url)
        if not username:
            username = self.config.identity.admin_username
        if not password:
            password = self.config.identity.admin_password
        tenant_id = [
            tenant.id for tenant in self.identity_client.tenants.list()
            if tenant.name == tenant_name][0]
        return saharaclient.client.Client(self.config.savanna.api_version,
                                          username=username,
                                          api_key=password,
                                          project_name=tenant_name,
                                          auth_url=auth_url,
                                          sahara_url="{url}/{id}".format(
                                              url=savanna_url, id=tenant_id))

    def _get_ceilometer_client(self):
        keystone = self._get_identity_client()
        try:
            endpoint = keystone.service_catalog.url_for(
                service_type='metering',
                endpoint_type='publicURL')
        except keystoneclient.exceptions.EndpointNotFound:
            LOG.warning('Can not initialize ceilometer client')
            return None

        return ceilometerclient.v2.Client(endpoint=endpoint,
                                          token=lambda: keystone.auth_token)


class OfficialClientTest(fuel_health.test.TestCase):
    manager_class = OfficialClientManager

    @classmethod
    def _create_nano_flavor(cls):
        name = rand_name('ost1_test-flavor-nano')
        flavorid = rand_int_id(999, 10000)
        try:
            flavor = cls.compute_client.flavors.create(
                name, 64, 1, 1, flavorid)
        except Exception:
            LOG.debug("OSTF test flavor cannot be created.")
            LOG.debug(traceback.format_exc())
        return flavor

    def get_image_from_name(self):
        image_name = self.manager.config.compute.image_name
        images = [i for i in self.compute_client.images.list()
                  if i.status.lower() == 'active']
        image_id = ''
        LOG.debug(images)
        if images:
            for im in images:
                LOG.debug(im.name)
                if (im.name and
                        im.name.strip().lower() ==
                        image_name.strip().lower()):
                    image_id = im.id
        if not image_id:
            raise exceptions.ImageFault
        return image_id

    def _delete_server(self, server):
        LOG.debug("Deleting server.")
        self.compute_client.servers.delete(server)

        def is_deletion_complete():
            try:
                server.get()
            except Exception as e:
                if e.__class__.__name__ == 'NotFound':
                    return True
                LOG.debug(traceback.format_exc())
                return False

        fuel_health.test.call_until_true(
            is_deletion_complete, 20, 10)

    def retry_command(self, retries, timeout, method, *args, **kwargs):
        for i in range(retries):
            try:
                result = method(*args, **kwargs)
                LOG.debug("Command execution successful.")
                return result
            except Exception as exc:
                LOG.debug(traceback.format_exc())
                LOG.debug("%s. Another"
                          " effort needed." % exc)
                time.sleep(timeout)

        self.fail("Instance is not reachable by IP.")

    def check_clients_state(self):
        if not self.manager.clients_initialized:
            LOG.debug("Unable to initialize Keystone client: {trace}".format(
                trace=self.manager.traceback))
            if self.manager.keystone_error_message:
                self.fail(self.manager.keystone_error_message)
            else:
                self.fail("Keystone client is not available. Please, refer "
                          "to OpenStack logs to fix this problem")

    def check_image_exists(self):
        try:
            self.get_image_from_name()
        except exceptions.ImageFault as exc:
            LOG.debug(exc)
            self.fail("{image} image not found. Please, download "
                      "http://download.cirros-cloud.net/0.3.1/"
                      "cirros-0.3.1-x86_64-disk.img image and "
                      "register it in Glance with name '{image}' as "
                      "'admin' tenant.".format(
                          image=self.manager.config.compute.image_name))

    @classmethod
    def tearDownClass(cls):
        cls.error_msg = []
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
                LOG.debug(traceback.format_exc())

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
                    LOG.debug(traceback.format_exc())
                return False

            # Block until resource deletion has completed or timed-out
            fuel_health.test.call_until_true(is_deletion_complete, 20, 10)


class NovaNetworkScenarioTest(OfficialClientTest):
    """
    Base class for nova network scenario tests
    """

    @classmethod
    def setUpClass(cls):
        super(NovaNetworkScenarioTest, cls).setUpClass()
        if cls.manager.clients_initialized:
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
            cls.error_msg = []
            cls.private_net = 'net04'

    def setUp(self):
        super(NovaNetworkScenarioTest, self).setUp()
        self.check_clients_state()

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
                LOG.debug(traceback.format_exc())
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

    @classmethod
    def _clear_networks(cls):
        try:
            for net in cls.network:
                cls.compute_client.networks.delete(net)
        except Exception as exc:
            cls.error_msg.append(exc)
            LOG.debug(traceback.format_exc())
            pass

    def _list_networks(self):
        nets = self.compute_client.networks.list()
        return nets

    def _create_server(self, client, name, security_groups):
        base_image_id = self.get_image_from_name()
        if 'neutron' in self.config.network.network_provider:
            network = [net.id for net in
                       self.compute_client.networks.list()
                       if net.label == self.private_net]

            if network:
                create_kwargs = {'nics': [{'net-id': network[0]}],
                                 'security_groups': security_groups}
            else:
                self.fail('Private network was not created by default')
        else:
            create_kwargs = {'security_groups': security_groups}

        server = client.servers.create(name, base_image_id,
                                       self.nova_netw_flavor.id,
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
        self.servers.append(server)
        return server

    def _create_floating_ip(self):
        floating_ips_pool = self.compute_client.floating_ip_pools.list()

        if floating_ips_pool:
            floating_ip = self.compute_client.floating_ips.create(
                pool=floating_ips_pool[0].name)
            return floating_ip
        else:
            self.fail('No available floating IP found')

    def _assign_floating_ip_to_instance(self, client, server, floating_ip):
        try:
            client.servers.add_floating_ip(server, floating_ip)
        except Exception:
            LOG.debug(traceback.format_exc())
            self.fail('Can not assign floating ip to instance')

    @classmethod
    def _clean_floating_ips(cls):
        if cls.floating_ips:
            for ip in cls.floating_ips:
                LOG.info('Floating_ip_for_deletion{0}'.format(
                    cls.floating_ips))
                try:
                    cls.compute_client.floating_ips.delete(ip)
                except Exception as exc:
                    cls.error_msg.append(exc)
                    LOG.debug(traceback.format_exc())
                    pass

    def _ping_ip_address(self, ip_address, timeout, retries):
        def ping():
            cmd = "ping -q -c1 -w10 %s" % ip_address

            if self.host:
                try:
                    ssh = SSHClient(self.host[0],
                                    self.usr, self.pwd,
                                    key_filename=self.key,
                                    timeout=timeout)
                except Exception as exc:
                    LOG.debug(traceback.format_exc())

                return self.retry_command(retries[0], retries[1],
                                          ssh.exec_command, cmd)

            else:
                self.fail('Wrong tests configurations, one from the next '
                          'parameters are empty controller_node_name or '
                          'controller_node_ip ')

        # TODO Allow configuration of execution and sleep duration.
        return fuel_health.test.call_until_true(ping, 40, 1)

    def _ping_ip_address_from_instance(self, ip_address, timeout,
                                       retries, viaHost=None):
        def ping():

            if not (self.host or viaHost):
                self.fail('Wrong tests configurations, one from the next '
                          'parameters are empty controller_node_name or '
                          'controller_node_ip ')
            try:
                host = viaHost or self.host[0]
                LOG.debug('Get ssh to instance')
                ssh = SSHClient(host,
                                self.usr, self.pwd,
                                key_filename=self.key,
                                timeout=timeout)

            except Exception as exc:
                LOG.debug(traceback.format_exc())

            command = "ping -q -c1 -w10 8.8.8.8"

            return self.retry_command(retries[0], retries[1],
                                      ssh.exec_command_on_vm,
                                      command=command,
                                      user='cirros',
                                      password='cubswin:)',
                                      vm=ip_address)

        # TODO Allow configuration of execution and sleep duration.
        return fuel_health.test.call_until_true(ping, 40, 1)

    def _check_vm_connectivity(self, ip_address, timeout, retries):
        self.assertTrue(self._ping_ip_address(ip_address, timeout, retries),
                        "Timed out waiting for %s to become "
                        "reachable. Please, check Network "
                        "configuration" % ip_address)

    def _check_connectivity_from_vm(self, ip_address,
                                    timeout, retries,
                                    viaHost=None):
        self.assertTrue(self._ping_ip_address_from_instance(ip_address,
                                                            timeout, retries,
                                                            viaHost=viaHost),
                        "Timed out waiting for %s to become "
                        "reachable. Please, check Network "
                        "configuration" % ip_address)

    @classmethod
    def tearDownClass(cls):
        super(NovaNetworkScenarioTest, cls).tearDownClass()
        if cls.manager.clients_initialized:
            cls._clean_floating_ips()
            cls._clear_networks()


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
        self.check_clients_state()
        if not self._enabled:
            self.fail('Nova Networking is not available')

    @classmethod
    def setUpClass(cls):
        super(SanityChecksTest, cls).setUpClass()
        if cls.manager.clients_initialized:
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

    def _list_stacks(self, client):
        return client.stacks.list()


class SmokeChecksTest(OfficialClientTest):
    """
    Base class for openstack smoke tests
    """

    @classmethod
    def setUpClass(cls):
        super(SmokeChecksTest, cls).setUpClass()
        if cls.manager.clients_initialized:
            cls.tenant_id = cls.manager._get_identity_client(
                cls.config.identity.admin_username,
                cls.config.identity.admin_password,
                cls.config.identity.admin_tenant_name).tenant_id
            cls.build_interval = cls.config.volume.build_interval
            cls.build_timeout = cls.config.volume.build_timeout
            cls.flavors = []
            cls.error_msg = []
            cls.private_net = 'net04'
            cls.smoke_flavor = ''
        else:
            cls.proceed = False

    def setUp(self):
        super(SmokeChecksTest, self).setUp()
        self.check_clients_state()

    def _create_flavors(self, client, ram, disk, vcpus=1):
        name = rand_name('ost1_test-flavor-')
        flavorid = rand_int_id()
        flavor = client.flavors.create(name=name, ram=ram, disk=disk,
                                       vcpus=vcpus, flavorid=flavorid)
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
                    LOG.debug(traceback.format_exc())
                    pass

    def _create_tenant(self, client):
        name = rand_name('ost1_test-tenant-')
        tenant = client.tenants.create(name)
        self.set_resource(name, tenant)
        return tenant

    def _create_user(self, client, tenant_id):
        password = "123456"
        email = "test@test.com"
        name = rand_name('ost1_test-user-')
        user = client.users.create(name, password, email, tenant_id)
        self.set_resource(name, user)
        return user

    def _create_role(self, client):
        name = rand_name('ost1_test-role-')
        role = client.roles.create(name)
        self.set_resource(name, role)
        return role

    def _create_volume(self, client):
        display_name = rand_name('ost1_test-volume')
        volume = client.volumes.create(size=1, display_name=display_name)
        self.set_resource(display_name, volume)
        return volume

    def _create_server(self, client):
        name = rand_name('ost1_test-volume-instance')
        base_image_id = self.get_image_from_name()
        if 'neutron' in self.config.network.network_provider:
            network = [net.id for net in
                       self.compute_client.networks.list()
                       if net.label == self.private_net]
            if network:
                create_kwargs = {'nics': [{'net-id': network[0]}]}
            else:
                self.fail('Private network was not created by default')
            server = client.servers.create(
                name, base_image_id, self.smoke_flavor.id, **create_kwargs)
        else:
            server = client.servers.create(name, base_image_id,
                                           self.smoke_flavor.id)

        self.verify_response_body_content(server.name,
                                          name,
                                          "Instance creation failed")
        # The instance retrieved on creation is missing network
        # details, necessitating retrieval after it becomes active to
        # ensure correct details.
        server = self._wait_server_param(client, server, 'addresses', 5, 1)
        self.set_resource(name, server)
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

    def _detach_volume(self, server, volume):
        volume = self.compute_client.volumes.delete_server_volume(
            server_id=server, attachment_id=volume)
        return volume

    def verify_volume_deletion(self, volume):

        def is_volume_deleted():
            try:
                self.compute_client.volumes.get(volume.id)
            except Exception as e:
                if e.__class__.__name__ == 'NotFound':
                    return True
                return False

        fuel_health.test.call_until_true(is_volume_deleted, 20, 10)

    @classmethod
    def tearDownClass(cls):
        super(SmokeChecksTest, cls).tearDownClass()
        if cls.manager.clients_initialized:
            cls._clean_flavors()
            if cls.smoke_flavor:
                try:
                    cls.compute_client.flavors.delete(cls.smoke_flavor)
                except Exception:
                    LOG.debug("OSTF test flavor cannot be deleted.")
                    LOG.debug(traceback.format_exc())
