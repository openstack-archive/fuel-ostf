# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack, LLC
# Copyright 2013 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import traceback

from fuel_health.common.utils.data_utils import rand_name
from fuel_health import nmanager

LOG = logging.getLogger(__name__)


class TestNovaNetwork(nmanager.NovaNetworkScenarioTest):
    """
    Test suit verifies:
     - keypairs creation
     - security groups creation
     - Network creation
     - Instance creation
     - Floating ip creation
     - Instance connectivity by floating IP
    """
    @classmethod
    def setUpClass(cls):
        super(TestNovaNetwork, cls).setUpClass()
        if cls.manager.clients_initialized:
            cls.nova_netw_flavor = cls._create_nano_flavor()
            cls.tenant_id = cls.manager._get_identity_client(
                cls.config.identity.admin_username,
                cls.config.identity.admin_password,
                cls.config.identity.admin_tenant_name).tenant_id
            cls.keypairs = {}
            cls.security_groups = {}
            cls.network = []
            cls.servers = []
            cls.floating_ips = []

    def setUp(self):
        super(TestNovaNetwork, self).setUp()
        # if not self.manager.clients_initialized:
        #     LOG.debug("Unable to initialize Keystone client: %s"
        #               % self.manager.traceback)
        #     self.fail("Keystone is not available. Please,"
        #               " refer to OpenStack logs to fix this problem.")
        self.check_clients_state()
        if not self.config.compute.compute_nodes:
            self.fail('There are no compute nodes')

    @classmethod
    def tearDownClass(cls):
        super(TestNovaNetwork, cls).tearDownClass()
        if cls.manager.clients_initialized:
            if cls.manager.clients_initialized:
                try:
                    cls.compute_client.flavors.delete(cls.nova_netw_flavor.id)
                except Exception:
                    LOG.debug(traceback.format_exc())

    def tearDown(self):
        super(TestNovaNetwork, self).tearDown()
        if self.manager.clients_initialized:
            if self.servers:
                for server in self.servers:
                    try:
                        self._delete_server(server)
                        self.servers.remove(server)
                    except Exception:
                        LOG.debug(traceback.format_exc())
                        LOG.debug("Server was already deleted.")

    def test_001_create_keypairs(self):
        """Create keypair
        Target component: Nova.

        Scenario:
            1. Create a new keypair, check if it was created successfully.
        Duration: 25 s.

        """
        self.keypairs[self.tenant_id] = self.verify(25,
                                                    self._create_keypair,
                                                    1,
                                                    'Keypair can not be'
                                                    ' created.',
                                                    'keypair creation',
                                                    self.compute_client)

    def test_002_create_security_groups(self):
        """Create security group
        Target component: Nova

        Scenario:
            1. Create a security group, check if it was created correctly.
        Duration: 25 s.

        """
        self.security_groups[self.tenant_id] = self.verify(
            25, self._create_security_group, 1,
            "Security group can not be created.",
            'security group creation',
            self.compute_client)

    def test_003_check_networks(self):
        """Check network parameters
        Target component: Nova

        Scenario:
            1. Get the list of networks.
            2. Confirm that networks have expected labels.
            3. Confirm that networks have expected ids.
        Duration: 50 s.

        """
        seen_nets = self.verify(
            50,
            self._list_networks,
            1,
            "List of networks is not available.",
            'listing networks'
        )
        seen_labels, seen_ids = zip(*((n.label, n.id) for n in seen_nets))
        for mynet in self.network:
            self.verify_response_body(seen_labels, mynet.label,
                                      ('Network can not be created.'
                                       'properly'), failed_step=2)
            self.verify_response_body(seen_ids, mynet.id,
                                      ('Network can not be created.'
                                       ' properly '), failed_step=3)

    def test_004_create_servers(self):
        """Launch instance
        Target component: Nova

        Scenario:
            1. Create a new security group (if it doesn`t exist yet).
            2. Create an instance using the new security group.
            3. Delete instance.
        Duration: 200 s.

        """
        if not self.security_groups:
            self.security_groups[self.tenant_id] = self.verify(
                25,
                self._create_security_group,
                1,
                "Security group can not be created.",
                'security group creation',
                self.compute_client)

        name = rand_name('ost1_test-server-smoke-')
        security_groups = [self.security_groups[self.tenant_id].name]

        server = self.verify(
            200,
            self._create_server,
            2,
            "Creating instance using the new security group has failed.",
            'image creation',
            self.compute_client, name, security_groups
        )

        self.verify(30, self._delete_server, 3,
                    "Server can not be deleted.",
                    "server deletion", server)

    def test_005_check_public_network_connectivity(self):
        """Check that VM is accessible via floating IP address
        Target component: Nova

        Scenario:
            1. Create a new security group (if it doesn`t exist yet).
            2. Create an instance using the new security group
            3. Create a new floating IP
            4. Assign the new floating IP to the instance.
            5. Check connectivity to the floating IP using ping command.
            6. Remove server floating ip.
            7. Delete server.
        Duration: 300 s.

        """
        if not self.security_groups:
                self.security_groups[self.tenant_id] = self.verify(
                    25, self._create_security_group, 1,
                    "Security group can not be created.",
                    'security group creation',
                    self.compute_client)

        name = rand_name('ost1_test-server-smoke-')
        security_groups = [self.security_groups[self.tenant_id].name]

        server = self.verify(200, self._create_server, 2,
                             "Server can not be created.",
                             "server creation",
                             self.compute_client, name, security_groups)

        floating_ip = self.verify(
            20,
            self._create_floating_ip,
            3,
            "Floating IP can not be created.",
            'floating IP creation')

        self.verify(10, self._assign_floating_ip_to_instance,
                    4, "Floating IP can not be assigned.",
                    'floating IP assignment',
                    self.compute_client, server, floating_ip)

        self.floating_ips.append(floating_ip)

        self.verify(250, self._check_vm_connectivity, 5,
                    "VM connectivity doesn`t function properly.",
                    'VM connectivity checking', floating_ip.ip,
                    30, (4, 30))

        self.verify(10, self.compute_client.servers.remove_floating_ip,
                    6, "Floating IP cannot be removed.",
                    "removing floating IP", server, floating_ip)

        self.floating_ips.remove(floating_ip)

        self.verify(30, self._delete_server, 7,
                    "Server can not be deleted. ",
                    "server deletion", server)

    def test_008_check_public_instance_connectivity_from_instance(self):
        """Check network connectivity from instance via floating IP
        Target component: Nova

        Scenario:
            1. Create a new security group (if it doesn`t exist yet).
            2. Create an instance using the new security group.
            3. Create a new floating IP
            4. Assign the new floating IP to the instance.
            5. Check that public IP 8.8.8.8 can be pinged from instance.
            6. Remove server floating ip.
            7. Delete server.
        Duration: 300 s.

        """
        if not self.security_groups:
                self.security_groups[self.tenant_id] = self.verify(
                    25, self._create_security_group, 1,
                    "Security group can not be created.",
                    'security group creation',
                    self.compute_client)

        name = rand_name('ost1_test-server-smoke-')
        security_groups = [self.security_groups[self.tenant_id].name]

        server = self.verify(200, self._create_server, 2,
                             "Server can not be created.",
                             "server creation",
                             self.compute_client, name, security_groups)

        floating_ip = self.verify(
            20,
            self._create_floating_ip,
            3,
            "Floating IP can not be created.",
            'floating IP creation')

        self.verify(10, self._assign_floating_ip_to_instance,
                    4, "Floating IP can not be assigned.",
                    'floating IP assignment',
                    self.compute_client, server, floating_ip)

        self.floating_ips.append(floating_ip)

        ip_address = floating_ip.ip
        LOG.info('is address is %s' % ip_address)
        LOG.debug(ip_address)
        self.verify(250, self._check_connectivity_from_vm,
                    5, ("Connectivity to 8.8.8.8 from the VM doesn`t "
                    "function properly."),
                    'public connectivity checking from VM', ip_address,
                    30, (4, 30))

        self.verify(10, self.compute_client.servers.remove_floating_ip,
                    6, "Floating IP cannot be removed.",
                    "removing floating IP", server, floating_ip)

        self.floating_ips.remove(floating_ip)

        self.verify(30, self._delete_server, 7,
                    "Server can not be deleted. ",
                    "server deletion", server)

    def test_006_check_internet_connectivity_instance_without_floatingIP(self):
        """Check network connectivity from instance without floating IP
        Target component: Nova

        Scenario:
            1. Create a new security group (if it doesn`t exist yet).
            2. Create an instance using the new security group.
            (if it doesn`t exist yet).
            3. Check that public IP 8.8.8.8 can be pinged from instance.
            4. Delete server.
        Duration: 300 s.

        Deployment tags: nova_network
        """
        if not self.security_groups:
            self.security_groups[self.tenant_id] = self.verify(
                25, self._create_security_group, 1,
                "Security group can not be created.",
                'security group creation', self.compute_client)

        name = rand_name('ost1_test-server-smoke-')
        security_groups = [self.security_groups[self.tenant_id].name]

        server = self.verify(
            200, self._create_server, 2,
            "Server can not be created.",
            'server creation',
            self.compute_client, name, security_groups)

        try:
            for addr in server.addresses:
                if addr.startswith('novanetwork'):
                    instance_ip = server.addresses[addr][0]['addr']
            compute = getattr(server, 'OS-EXT-SRV-ATTR:host')
        except Exception as e:
            LOG.debug(traceback.format_exc())
            self.fail("Step 3 failed: cannot get instance details. "
                      "Please refer to OpenStack logs for more details.")

        self.verify(250, self._check_connectivity_from_vm,
                    3, ("Connectivity to 8.8.8.8 from the VM doesn`t "
                        "function properly."),
                    'public connectivity checking from VM',
                    instance_ip, 30, (4, 30), compute)

        self.verify(30, self._delete_server, 5,
                    "Server can not be deleted. ",
                    "server deletion", server)
