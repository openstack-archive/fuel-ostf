from fuel_health.common.utils.data_utils import rand_name
from fuel_health import nmanager
from fuel_health.test import attr


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
            msg = 'Either tenant_networks_reachable must be "true.'
            cls.enabled = False
            raise cls.skipException(msg)

    @classmethod
    def setUpClass(cls):
        super(TestNovaNetwork, cls).setUpClass()
        cls.check_preconditions()
        cls.tenant_id = cls.manager._get_identity_client(
            cls.config.identity.username,
            cls.config.identity.password,
            cls.config.identity.tenant_name).tenant_id

        cls.keypairs = {}
        cls.security_groups = {}
        cls.network = []
        cls.servers = []
        cls.floating_ips = []

    @attr(type=['fuel', 'smoke'])
    def test_001_create_keypairs(self):
        """ Test verifies keypair creation """
        self.keypairs[self.tenant_id] = self._create_keypair(
            self.compute_client)

    @attr(type=['fuel', 'smoke'])
    def test_002_create_security_groups(self):
        """Test verifies security group creation"""
        self.security_groups[self.tenant_id] = self._create_security_group(
            self.compute_client)

    @attr(type=['fuel', 'smoke'])
    def test_003_create_networks(self):
        """Test verifies network creation"""
        networks = self._create_network()
        self.network.append(networks)

    @attr(type=['fuel', 'smoke'])
    def test_004_check_networks(self):
        """Test verifies created network"""
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
                                      ('Network does is created'
                                       ' properly '))

    @attr(type=['fuel', 'smoke'])
    def test_005_create_servers(self):
        """
         Test verifies instance creation
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

        #for i, network in enumerate(self.networks):
        name = rand_name('ost1_test-server-smoke-')
        keypair_name = self.keypairs[self.tenant_id].name
        security_groups = [self.security_groups[self.tenant_id].name]

        server = self._create_server(self.compute_client,
                                         name, keypair_name, security_groups)
        self.servers.append(server)

    @attr(type=['fuel', 'smoke'])
    def test_006_check_tenant_network_connectivity(self):
        """
        Test verifies created network connectivity
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
    def test_007_assign_floating_ips(self):
        """
        Test verifies assignment of floating ip to created instance
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
    def test_008_check_public_network_connectivity(self):
        """
        Test verifies network connectivity trough floating ip
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
