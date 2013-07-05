
from fuel_health.common import network_common as net_common
from fuel_health.common.utils.data_utils import rand_name
from fuel_health import nmanager
from fuel_health.test import attr


class TestNovaNetwork(nmanager.NovaNetworkScenarioTest):

    """
    This smoke test suite assumes that Nova has been configured to
    boot VM's with Quantum-managed networking, and attempts to
    verify network connectivity as follows:

     * For a freshly-booted VM with an IP address ("port") on a given network:

       - host can ping the IP address.  This implies, but
         does not guarantee (see the ssh check that follows), that the
         VM has been assigned the correct IP address and has
         connectivity to  host.

       - the host can perform key-based authentication to an
         ssh server hosted at the IP address.  This check guarantees
         that the IP address is associated with the target VM.

       #TODO(mnewby) - Need to implement the following:
       - the host can ssh into the VM via the IP address and
         successfully execute the following:

         - ping an external IP address, implying external connectivity.

         - ping an external hostname, implying that dns is correctly
           configured.


     There are presumed to be two types of networks: tenant and
     public.  A tenant network may or may not be reachable from the
     host.  A public network is assumed to be reachable from
     the host, and it should be possible to associate a public
     ('floating') IP address with a tenant ('fixed') IP address to
     faciliate external connectivity to a potentially unroutable
     tenant IP address.

     This test suite can be configured to test network connectivity to
     a VM via a tenant network, a public network, or both.  If both
     networking types are to be evaluated, tests that need to be
     executed remotely on the VM (via ssh) will only be run against
     one of the networks (to minimize test execution time).

     Determine which types of networks to test as follows:

     * Configure tenant network checks (via the
       'tenant_networks_reachable' key) if the  host should
       have direct connectivity to tenant networks.  This is likely to
       be the case if test is running on the same host as a
       single-node devstack installation with IP namespaces disabled.

     * Configure checks for a public network if a public network has
       been configured prior to the test suite being run and if the
       host should have connectivity to that public network.
       Checking connectivity for a public network requires that a
       value be provided for 'public_network_id'.  A value can
       optionally be provided for 'public_router_id' if tenants will
       use a shared router to access a public network (as is likely to
       be the case when IP namespaces are not enabled).  If a value is
       not provided for 'public_router_id', a router will be created
       for each tenant and use the network identified by
       'public_network_id' as its gateway.

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
        cls.networks = []
        cls.servers = []
        cls.floating_ips = {}

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
        network = self._create_network(self.tenant_id)
        self.networks.append(network)

    @attr(type=['fuel', 'smoke'])
    def test_004_check_networks(self):
        """Test verifies created network"""
        seen_nets = self._list_networks()
        seen_labels = [n.label for n in seen_nets]
        seen_ids = [n.id for n in seen_nets]
        for mynet in self.networks:
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
        if not (self.keypairs or self.security_groups or self.networks):
            raise self.skipTest('Necessary resources have not been defined')
        for i, network in enumerate(self.networks):
            name = rand_name('ost1_test-server-smoke-%d-' % i)
            keypair_name = self.keypairs[self.tenant_id].name
            security_groups = [self.security_groups[self.tenant_id].name]
            server = self._create_server(self.compute_client, network,
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
            raise self.skipTest("No VM's have been created")
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
            raise self.skipTest("No VM's have been created")
        for server in self.servers:
            floating_ip = self._create_floating_ip(server)
            self.floating_ips.setdefault(server, [])
            self.floating_ips[server].append(floating_ip)

    @attr(type=['fuel', 'smoke'])
    def test_008_check_public_network_connectivity(self):
        """
        Test verifies network connectivity trough floating ip
        """
        if not self.floating_ips:
            raise self.skipTest('No floating ips have been allocated.')
        # The target login is assumed to have been configured for
        # key-based authentication by cloud-init.
        ssh_login = self.config.compute.image_ssh_user
        private_key = self.keypairs[self.tenant_id].private_key
        for server, floating_ips in self.floating_ips.iteritems():
            for floating_ip in floating_ips:
                ip_address = floating_ip.ip
                self._check_vm_connectivity(ip_address, ssh_login, private_key)
