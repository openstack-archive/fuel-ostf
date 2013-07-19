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
import netaddr
import time

from fuel_health import clients
from fuel_health import exceptions
from fuel_health.common import log as logging
from fuel_health.common.utils.data_utils import rand_name
import fuel_health.test


LOG = logging.getLogger(__name__)

def error(message):
        LOG.error(message)

class BaseComputeTest(fuel_health.test.BaseTestCase):
    """Base test case class for all Compute API tests."""

    @classmethod
    def setUpClass(cls):
        os = clients.Manager(interface=cls._interface)

        cls.os = os
        cls.servers_client = os.servers_client
        cls.flavors_client = os.flavors_client
        cls.images_client = os.images_client
        cls.floating_ips_client = os.floating_ips_client
        cls.keypairs_client = os.keypairs_client
        cls.security_groups_client = os.security_groups_client
        cls.quotas_client = os.quotas_client
        cls.limits_client = os.limits_client
        cls.volumes_client = os.volumes_client
        cls.snapshots_client = os.snapshots_client
        cls.fixed_ips_client = os.fixed_ips_client
        cls.services_client = os.services_client
        cls.build_interval = cls.config.compute.build_interval
        cls.build_timeout = cls.config.compute.build_timeout
        cls.ssh_user = cls.config.compute.ssh_user
        cls.servers = []

        cls.servers_client_v3_auth = os.servers_client_v3_auth

    @classmethod
    def _get_identity_admin_client(cls):
        """
        Returns an instance of the Identity Admin API client
        """
        os = clients.AdminManager(interface=cls._interface)
        admin_client = os.identity_client
        return admin_client

    def wait_for(self, condition):
        """Repeatedly calls condition() until a timeout."""
        start_time = int(time.time())
        while True:
            try:
                condition()
            except Exception:
                pass
            else:
                return
            if int(time.time()) - start_time >= self.build_timeout:
                condition()
                return
            time.sleep(self.build_interval)


class BaseComputeAdminTest(BaseComputeTest):
    """Base test case class for all Compute Admin API tests."""

    @classmethod
    def setUpClass(cls):
        super(BaseComputeAdminTest, cls).setUpClass()
        admin_username = cls.config.compute_admin.username
        admin_password = cls.config.compute_admin.password
        admin_tenant = cls.config.compute_admin.tenant_name

        if not (admin_username and admin_password and admin_tenant):
            msg = ("Missing Compute Admin API credentials "
                   "in configuration.")
            raise cls.skipException(msg)

        cls.os_adm = clients.ComputeAdminManager(interface=cls._interface)


class BaseIdentityAdminTest(fuel_health.test.BaseTestCase):

    @classmethod
    def setUpClass(cls):
        os = clients.AdminManager(interface=cls._interface)
        cls.client = os.identity_client
        cls.token_client = os.token_client
        cls.service_client = os.services_client

        if not cls.client.has_admin_extensions():
            raise cls.skipException("Admin extensions disabled")

        cls.data = DataGenerator(cls.client)

        os = clients.Manager(interface=cls._interface)
        cls.non_admin_client = os.identity_client

    @classmethod
    def tearDownClass(cls):
        cls.data.teardown_all()

    def disable_user(self, user_name):
        user = self.get_user_by_name(user_name)
        self.client.enable_disable_user(user['id'], False)

    def disable_tenant(self, tenant_name):
        tenant = self.get_tenant_by_name(tenant_name)
        self.client.update_tenant(tenant['id'], enabled=False)

    def get_user_by_name(self, name):
        _, users = self.client.get_users()
        user = [u for u in users if u['name'] == name]
        if len(user) > 0:
            return user[0]

    def get_tenant_by_name(self, name):
        _, tenants = self.client.list_tenants()
        tenant = [t for t in tenants if t['name'] == name]
        if len(tenant) > 0:
            return tenant[0]

    def get_role_by_name(self, name):
        _, roles = self.client.list_roles()
        role = [r for r in roles if r['name'] == name]
        if len(role) > 0:
            return role[0]


class DataGenerator(object):

        def __init__(self, client):
            self.client = client
            self.users = []
            self.tenants = []
            self.roles = []
            self.role_name = None

        def setup_test_user(self):
            """Set up a test user."""
            self.setup_test_tenant()
            self.test_user = rand_name('ost1_test-user_')
            self.test_password = rand_name('pass_')
            self.test_email = self.test_user + '@testmail.tm'
            resp, self.user = self.client.create_user(self.test_user,
                                                      self.test_password,
                                                      self.tenant['id'],
                                                      self.test_email)
            self.users.append(self.user)

        def setup_test_tenant(self):
            """Set up a test tenant."""
            self.test_tenant = rand_name('ost1_test-tenant_')
            self.test_description = rand_name('desc_')
            resp, self.tenant = self.client.create_tenant(
                name=self.test_tenant,
                description=self.test_description)
            self.tenants.append(self.tenant)

        def setup_test_role(self):
            """Set up a test role."""
            self.test_role = rand_name('ost1_test-role')
            resp, self.role = self.client.create_role(self.test_role)
            self.roles.append(self.role)

        def teardown_all(self):
            for user in self.users:
                self.client.delete_user(user['id'])
            for tenant in self.tenants:
                self.client.delete_tenant(tenant['id'])
            for role in self.roles:
                self.client.delete_role(role['id'])


class BaseNetworkTest(BaseIdentityAdminTest):

    @classmethod
    def setUpClass(cls):
        os = clients.AdminManager()
        cls.network_cfg = os.config.network
        cls.client = os.network_client
        cls.networks = []
        cls.subnets = []

    @classmethod
    def tearDownClass(cls):
        for subnet in cls.subnets:
            cls.client.delete_subnet(subnet['id'])
        for network in cls.networks:
            cls.client.delete_network(network['id'])

    @classmethod
    def create_network(cls, network_name=None):
        """Wrapper utility that returns a test network."""
        network_name = network_name or rand_name('ost1_test-network-')

        resp, body = cls.client.create_network(network_name)
        network = body['network']
        cls.networks.append(network)
        return network

    @classmethod
    def create_subnet(cls, network):
        """Wrapper utility that returns a test subnet."""
        cidr = netaddr.IPNetwork(cls.network_cfg.tenant_network_cidr)
        mask_bits = cls.network_cfg.tenant_network_mask_bits
        # Find a cidr that is not in use yet and create a subnet with it
        for subnet_cidr in cidr.subnet(mask_bits):
            try:
                resp, body = cls.client.create_subnet(network['id'],
                                                      str(subnet_cidr))
                break
            except exceptions.BadRequest as e:
                is_overlapping_cidr = 'overlaps with another subnet' in str(e)
                if not is_overlapping_cidr:
                    raise
        subnet = body['subnet']
        cls.subnets.append(subnet)
        return subnet
