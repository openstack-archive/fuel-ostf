from nose.plugins.attrib import attr
from nose.tools import timed

from fuel_health.common.utils.data_utils import rand_name
from fuel_health import nmanager


class TestNovaNetwork(nmanager.NovaNetworkScenarioTest):

    """
    Test suit verifies:
     - keypairs creation
     - security groups creation
     - Network creation
     - Instance creation
     - Fixed network connectivity verification
     - Floating ip creation
     - Instance connectivity by floating ip
    """

    @classmethod
    def check_preconditions(cls):
        super(TestNovaNetwork, cls).check_preconditions()
        cfg = cls.config.network
        if not cfg.tenant_networks_reachable:
            msg = 'Either tenant networks reachable must be "true.'
            cls.enabled = False
            raise cls.skipException(msg)

    @classmethod
    def setUpClass(cls):
        super(TestNovaNetwork, cls).setUpClass()
        cls.check_preconditions()
        cls.tenant_id = cls.manager._get_identity_client(
            cls.config.identity.admin_username,
            cls.config.identity.admin_password,
            cls.config.identity.admin_tenant_name).tenant_id

        cls.keypairs = {}
        cls.security_groups = {}
        cls.network = []
        cls.servers = []
        cls.floating_ips = []

    @attr(type=['fuel', 'smoke'])
    @timed(20.5)
    def test_001_create_keypairs(self):
        """Test checks keypair can be created.
        Target component: Nova.

        Scenario:
            1. Create a new keypair.
            2. Check keypair attributes are correct.
        Duration: 10-25 s.
        """
        self.keypairs[self.tenant_id] = self._create_keypair(
            self.compute_client)

    @attr(type=['fuel', 'smoke'])
    @timed(20.5)
    def test_002_create_security_groups(self):
        """Test checks security group can be created.
        Target component: Nova

        Scenario:
            1. Create security group.
            2. Check security group attributes are correct.
        Duration: 2-25 s.
        """
        self.security_groups[self.tenant_id] = self._create_security_group(
            self.compute_client)

    @attr(type=['fuel', 'smoke'])
    @timed(45.5)
    def test_004_check_networks(self):
        """Test checks created network parameters.
        Target component: Nova

        Scenario:
            1. Get list of networks.
            2. Check seen network labels equal to expected ones.
            3. Check seen network ids equal to expected ones.
        Duration: 1-50 s.
        """
        seen_nets = self._list_networks()
        seen_labels = [n.label for n in seen_nets]
        seen_ids = [n.id for n in seen_nets]
        for mynet in self.network:
            self.verify_response_body(seen_labels,
                                      mynet.label,
                                      ('Network is not created '
                                       'properly'))
            self.verify_response_body(seen_ids,
                                      mynet.id,
                                      ('Network is not created'
                                       ' properly '))

    @attr(type=['fuel', 'smoke'])
    @timed(60.7)
    def test_005_create_servers(self):
        """Test checks instance instance can be created.
        Target component: Nova

        Scenario:
            1. Create new keypair (if it`s nonexistent yet).
            2. Create new sec group (if it`s nonexistent yet).
            3. Create instance with usage of created sec group
            and keypair.
        Duration: 50-65.8 s.
        """
        if not self.keypairs:
            try:
                self.keypairs[self.tenant_id] = self._create_keypair(
                    self.compute_client)
            except Exception:
                self.fail("Necessary resources for booting instance"
                          " has not been created")
        if not self.security_groups:
            try:
                self.security_groups[self.tenant_id] = \
                    self._create_security_group(self.compute_client)
            except Exception:
                self.fail("Necessary resources for booting instance"
                          " has not been created")

        name = rand_name('ost1_test-server-smoke-')
        keypair_name = self.keypairs[self.tenant_id].name
        security_groups = [self.security_groups[self.tenant_id].name]

        server = self._create_server(self.compute_client,
                                         name, keypair_name, security_groups)
        self.servers.append(server)

    @attr(type=['fuel', 'smoke'])
    @timed(45.9)
    def test_006_check_tenant_network_connectivity(self):
        """Test checks created network connectivity
        Target component: Nova.

        Scenario:
            1. Create new keypair (if it`s nonexistent yet).
            2. Create new sec group (if it`s nonexistent yet).
            3. Create server with usage of created sec group
            and keypair.
            4. Use ping command on newly created server ip.
        Duration: 40-55 s.
        """
        if not self.config.network.tenant_networks_reachable:
            msg = 'Tenant networks not configured to be reachable.'
            raise self.skipTest(msg)
        if not self.servers:
            if not self.keypairs:
                try:
                    self.keypairs[self.tenant_id] = self._create_keypair(
                        self.compute_client)
                except Exception:
                    self.fail("Necessary resources for booting instance"
                              " has not been created")
            if not self.security_groups:
                try:
                    self.security_groups[self.tenant_id] = \
                    self._create_security_group(self.compute_client)
                except Exception:
                    self.fail("Necessary resources for booting instance"
                              " has not been created")

            name = rand_name('ost1_test-server-smoke-')
            keypair_name = self.keypairs[self.tenant_id].name
            security_groups = [self.security_groups[self.tenant_id].name]

            server = self._create_server(self.compute_client,
                                         name, keypair_name, security_groups)
            self.servers.append(server)

        # The target login is assumed to have been configured for
        # key-based authentication by cloud-init.
        ssh_login = self.config.compute.image_ssh_user
        private_key = self.keypairs[self.tenant_id].private_key
        for server in self.servers:
            for net_name, ip_addresses in server.networks.iteritems():
                for ip_address in ip_addresses:
                    self._check_vm_connectivity(ip_address, ssh_login,
                                                private_key)

    @attr(type=['fuel', 'smoke'])
    @timed(49.9)
    def test_007_assign_floating_ips(self):
        """Test checks assignment of floating ip to created instance
        Target component: Nova

        Scenario:
            1. Create new keypair (if it`s nonexistent yet).
            2. Create new sec group (if it`s nonexistent yet).
            3. Create instance with usage of created sec group
            and keypair.
            4. Create new floatin ip.
            5. Assign floating ip to created instance.
        Duration: 40-55 s.
        """
        if not self.servers:
            if not self.keypairs:
                try:
                    self.keypairs[self.tenant_id] = self._create_keypair(
                        self.compute_client)
                except Exception:
                    self.fail("Necessary resources for booting instance"
                              " has not been created")
            if not self.security_groups:
                try:
                    self.security_groups[self.tenant_id] = self.\
                        _create_security_group(self.compute_client)
                except Exception:
                    self.fail("Necessary resources for booting instance"
                              " has not been created")

            name = rand_name('ost1_test-server-smoke-')
            keypair_name = self.keypairs[self.tenant_id].name
            security_groups = [self.security_groups[self.tenant_id].name]

            server = self._create_server(self.compute_client,
                                         name, keypair_name, security_groups)
            self.servers.append(server)
            floating_ip = self._create_floating_ip()

            self._assign_floating_ip_to_instance(
                self.compute_client, server, floating_ip)

            self.floating_ips.append(floating_ip)

    @attr(type=['fuel', 'smoke'])
    @timed(49.9)
    def test_008_check_public_network_connectivity(self):
        """Test checks network connectivity trough floating ip.
        Target component: Nova

        Scenario:
            1. Create new keypair (if it`s nonexistent yet).
            2. Create new sec group (if it`s nonexistent yet).
            3. Create instance with usage of created sec group
            and keypair.
            4. Check connectivity for all floating ips using
            ping command.
        Duration: 40-55 s.
        """
        if not self.floating_ips:
            if not self.servers:
                if not self.keypairs:
                    try:
                        self.keypairs[self.tenant_id] = self._create_keypair(
                            self.compute_client)
                    except Exception:
                        self.fail("Necessary resources for booting instance"
                                  " has not been created")
                if not self.security_groups:
                    try:
                        self.security_groups[self.tenant_id] = self.\
                            _create_security_group(self.compute_client)
                    except Exception:
                        self.fail("Necessary resources for booting instance"
                                  " has not been created")

                name = rand_name('ost1_test-server-smoke-')
                keypair_name = self.keypairs[self.tenant_id].name
                security_groups = [self.security_groups[self.tenant_id].name]

                server = self._create_server(
                    self.compute_client, name, keypair_name, security_groups)
                self.servers.append(server)
            for server in self.servers:
                floating_ip = self._create_floating_ip()
                self._assign_floating_ip_to_instance(
                    self.compute_client, server, floating_ip)
                self.floating_ips.append(floating_ip)

        # The target login is assumed to have been configured for
        # key-based authentication by cloud-init.
        ssh_login = self.config.compute.image_ssh_user
        private_key = self.keypairs[self.tenant_id].private_key
        for floating_ip in self.floating_ips:
            ip_address = floating_ip.ip
            self._check_vm_connectivity(ip_address, ssh_login, private_key)
