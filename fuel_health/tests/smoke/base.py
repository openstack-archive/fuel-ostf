import time

from fuel_health import clients
import fuel_health.test
from fuel_health.common import log as logging
from fuel_health.common.utils.data_utils import rand_name, rand_int_id
from fuel_health.tests import smoke
from fuel_health import nmanager


LOG = logging.getLogger(__name__)


class BaseComputeTest(fuel_health.test.BaseTestCase):
    """Base test case class for all Compute API tests."""

    conclusion = smoke.generic_setup_package()

    @classmethod
    def setUpClass(cls):
        cls.isolated_creds = []
        cls.keypairs = []
        cls.networks = []
        cls.sec_groups = []

        os = clients.AdminManager(interface=cls._interface)

        cls.os = os
        cls.servers_client = os.servers_client
        cls.flavors_client = os.flavors_client
        cls.images_client = os.images_client
        cls.floating_ips_client = os.floating_ips_client
        cls.keypairs_client = os.keypairs_client
        cls.security_groups_client = os.security_groups_client
        cls.quotas_client = os.quotas_client
        cls.volumes_client = os.volumes_client
        cls.snapshots_client = os.snapshots_client
        cls.interfaces_client = os.interfaces_client
        cls.fixed_ips_client = os.fixed_ips_client
        cls.services_client = os.services_client
        cls.build_interval = cls.config.compute.build_interval
        cls.build_timeout = cls.config.compute.build_timeout
        cls.ssh_user = cls.config.compute.ssh_user
        cls.flavor_ref = cls.config.compute.flavor_ref
        if os.config.network.quantum_available:
            cls.network_client = os.network_client

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

    @classmethod
    def clear_servers(cls):
        for server in cls.servers:
            try:
                cls.servers_client.delete_server(server['id'])
            except Exception:
                pass

        for server in cls.servers:
            try:
                cls.servers_client.wait_for_server_termination(server['id'])
            except Exception:
                pass

    @classmethod
    def create_server(cls, **kwargs):
        """Wrapper utility that returns a test server."""
        name = rand_name('ost1_test-' + cls.__name__ + "-instance")
        if 'name' in kwargs:
            name = kwargs.pop('name')
        flavor = kwargs.get('flavor', cls.flavor_ref)
        image_id = kwargs.get('image_id', nmanager.get_image_from_name())

        resp, body = cls.servers_client.create_server(
            name, image_id, flavor, **kwargs)

        # handle the case of multiple servers
        servers = [body]
        if 'min_count' in kwargs or 'max_count' in kwargs:
            # Get servers created which name match with name param.
            r, b = cls.servers_client.list_servers()
            servers = [s for s in b['servers'] if s['name'].startswith(name)]

        cls.servers.extend(servers)

        if 'wait_until' in kwargs:
            for server in servers:
                cls.servers_client.wait_for_server_status(
                    server['id'], kwargs['wait_until'])

        return resp, body

    @classmethod
    def tearDownClass(cls):
        cls.clear_servers()

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
        cls.flavors = []

        if not (admin_username and admin_password and admin_tenant):
            msg = ("Missing Compute Admin API credentials "
                   "in configuration.")
            raise cls.skipException(msg)

        cls.os_adm = clients.ComputeAdminManager(interface=cls._interface)

    @classmethod
    def create_flavor(cls, **kwargs):
        """
        Create test flavor.

        Arguments:
          - name: flavor name (must contain 'ost1_test' mask);
          - ram: flavor ram;
          - vcpus: TBD;
          - disk: flavor disk size;
          - flavor_id: unique flavor id;
          - ephemeral, swap, rxtx are optional params.
        """
        cls.client = cls.os_adm.flavors_client
        cls.user_client = cls.os.flavors_client
        new_flavor_id = rand_int_id(start=1000)
        name = 'ost1_test-flavor' + cls.__name__

        f_params = {'name': name,
                    'ram': 256,
                    'vcpus': 1,
                    'disk': 0,
                    'flav_id': new_flavor_id,
                    'ephemeral': 0,
                    'swap': 256,
                    'rxtx': 2
                    }

        for key in f_params.keys():
            if key in kwargs:
                f_params[key] = kwargs.pop(key)

        resp, body = cls.client.create_flavor(name=f_params['name'],
                                              ram=f_params['ram'],
                                              vcpus=f_params['vcpus'],
                                              disk=f_params['disk'],
                                              flavor_id=f_params['flav_id'],
                                              ephimeral=f_params['ephemeral'],
                                              swap=f_params['swap'],
                                              rxtx=f_params['rxtx'])
        cls.flavors.extend([body])

        return resp, body

    @classmethod
    def clear_flavors(cls):
        """
        Delete flavor verification test data.
        """
        for flavor in cls.flavors:
            try:
                cls.os_adm.flavors_client.delete_flavor(flavor['id'])
            except Exception:
                pass

    @classmethod
    def tearDownClass(cls):
        cls.clear_flavors()


class BaseIdentityAdminTest(fuel_health.test.BaseTestCase):

    @classmethod
    def setUpClass(cls):
        try:
            cls.flag = True
            os = clients.AdminManager(interface=cls._interface)
            cls.client = os.identity_client
            cls.token_client = os.token_client
            cls.service_client = os.services_client

            if not cls.client.has_admin_extensions():
                raise cls.skipException("Admin extensions disabled")

            cls.data = DataGenerator(cls.client)

            os = clients.Manager(interface=cls._interface)
            cls.non_admin_client = os.identity_client
        except Exception:
            cls.flag = False

    def setUp(self):
        super(BaseIdentityAdminTest, self).setUp()
        if not self.flag:
            self.fail("Can not get a Keystone")

    @classmethod
    def tearDownClass(cls):
        try:
            cls.teardown_flag = True
            cls.data.teardown_all()
        except Exception:
            cls.teardown_flag = False

    def tearDown(self):
        super(BaseIdentityAdminTest, self).tearDown()
        
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
            self.test_tenant = rand_name('ost1_test-test_tenant_')
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
