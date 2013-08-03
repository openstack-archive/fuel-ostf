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

from nose.plugins.attrib import attr

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
     - Instance connectivity by floating ip
    """

    @classmethod
    def check_preconditions(cls):
        super(TestNovaNetwork, cls).check_preconditions()
        cfg = cls.config.network
        if not cfg.tenant_networks_reachable:
            msg = 'Each tenant network must be reachable.'
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

    def setUp(self):
        super(TestNovaNetwork, self).setUp()
        if not self.config.compute.compute_nodes:
            self.fail('There are not compute nodes')

    @classmethod
    def tearDownClass(cls):
        super(TestNovaNetwork, cls).tearDownClass()

    @attr(type=['fuel', 'smoke'])
    def test_001_create_keypairs(self):
        """Keypair creation
        Target component: Nova.

        Scenario:
            1. Create a new keypair, check if it was created successfully.
        Duration: 10-25 s.
        """
        self.keypairs[self.tenant_id] = self.verify(25,
                                                    self._create_keypair,
                                                    1,
                                                    'Keypair can not be created.',
                                                    'keypair creation',
                                                    self.compute_client)

    @attr(type=['fuel', 'smoke'])
    def test_002_create_security_groups(self):
        """Security group creation
        Target component: Nova

        Scenario:
            1. Create security group, check if it was created correctly.
        Duration: 2-25 s.
        """
        self.security_groups[self.tenant_id] = self.verify(
            25, self._create_security_group, 1,
            "Security group can not be created.",
            'security group creation',
            self.compute_client)

    @attr(type=['fuel', 'smoke'])
    def test_004_check_networks(self):
        """Check network parameters
        Target component: Nova

        Scenario:
            1. Get list of networks.
            2. Check seen network labels equal to expected ones.
            3. Check seen network ids equal to expected ones.
        Duration: 1-50 s.
        """
        seen_nets = self.verify(
            50,
            self._list_networks,
            1,
            "List of networks is not available.",
            'networks listing'
        )
        seen_labels, seen_ids = zip(*((n.label, n.id) for n in seen_nets))
        for mynet in self.network:
            self.verify_response_body(seen_labels, mynet.label,
                                      ('Network can not be created.'
                                       'properly'), failed_step=2)
            self.verify_response_body(seen_ids, mynet.id,
                                      ('Network can not be created.'
                                       ' properly '), failed_step=3)

    @attr(type=['fuel', 'smoke'])
    def test_005_create_servers(self):
        """Launch instance
        Target component: Nova

        Scenario:
            1. Create new sec group (if it`s nonexistent yet).
            2. Create instance with usage of created sec group.
        Duration: 50-200 s.
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
            "Creating instance with usage of created security group failed.",
            'image creation',
            self.compute_client, name, security_groups
        )

        self.servers.append(server)

    @attr(type=['fuel', 'smoke'])
    def test_006_assign_floating_ips(self):
        """Assign floating IP
        Target component: Nova

        Scenario:
            1. Create new sec group (if it`s nonexistent yet).
            2. Create instance with usage of created sec group.
            3. Create new floating ip.
            4. Assign floating ip to created instance.
        Duration: 40-200 s.
        """
        if not self.servers:
            if not self.security_groups:
                self.security_groups[self.tenant_id] = self.verify(
                    25, self._create_security_group, 1,
                    "Security group can not be created.",
                    'security group creation',
                    self.compute_client)

            name = rand_name('ost1_test-server-smoke-')
            security_groups = [self.security_groups[self.tenant_id].name]

            server = self.verify(
                200,
                self._create_server,
                2,
                "Server can not be created.",
                "server creation",
                self.compute_client, name, security_groups
            )
            self.servers.append(server)

        floating_ip = self.verify(
            20,
            self._create_floating_ip,
            3,
            "Floating IP can not be created.",
            'floating IP creation')

        if self.servers:
            self.verify(
                10,
                self._assign_floating_ip_to_instance,
                4,
                "Floating IP can not be assigned.",
                'floating IP assignment',
                self.compute_client, self.servers[0], floating_ip)

        self.floating_ips.append(floating_ip)

    @attr(type=['fuel', 'smoke'])
    def test_007_check_public_network_connectivity(self):
        """Check that VM is accessible via floating IP address
        Target component: Nova

        Scenario:
            1. Create new sec group (if it`s nonexistent yet).
            2. Create instance with usage of created sec group.
            (if it`s nonexistent yet).
            3. Create new floating IP (if it`s nonexistent yet).
            4. Assign new floating IP to instance.
            5. Check connectivity for the floating ip using ping command.
        Duration: 40-200 s.
        """
        if not self.floating_ips:
            if not self.servers:
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

                self.servers.append(server)

            floating_ip = self.verify(20, self._create_floating_ip, 3,
                                      "Floating IP can not be created.",
                                      'floating IP creation')
            self.floating_ips.append(floating_ip)

        if self.servers and self.floating_ips:
            self.verify(10, self._assign_floating_ip_to_instance, 4,
                        "Floating IP can not be assigned.",
                        "floating IP assignment",
                        self.compute_client, self.servers[0], self.floating_ips[0])

        if self.floating_ips:
            ip_address = self.floating_ips[0].ip
            self.verify(100, self._check_vm_connectivity, 5,
                        "VM connectivity doesn`t function properly.",
                        'VM connectivity checking', ip_address)

    @attr(type=['fuel', 'smoke'])
    def test_008_check_public_instance_connectivity_from_instance(self):
        """Check network connectivity from instance via floating ip

        Scenario:
            1. Create new sec group (if it`s nonexistent yet).
            2. Create instance with usage of created sec group.
            (if it`s nonexistent yet).
            3. Create new floating IP (if it`s nonexistent yet).
            4. Assign new floating IP to instance.
            5. Ssh on instance from controller and execute ping command.
        Duration: 40-200 s.
        """
        if not self.floating_ips:
            if not self.servers:
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

                self.servers.append(server)

            floating_ip = self.verify(
                20, self._create_floating_ip, 3,
                "Floating IP can not be created.",
                'floating IP creation')

            self.floating_ips.append(floating_ip)

        if self.servers and self.floating_ips:
            self.verify(10, self._assign_floating_ip_to_instance, 4,
                    "Floating IP can not be assigned.",
                    "floating IP assignment",
                    self.compute_client, self.servers[0], self.floating_ips[0])

        if self.floating_ips:
            ip_address = self.floating_ips[0].ip
            LOG.debug(ip_address)
            self.verify(100, self._check_connectivity_from_vm,
                        5, ("Connectivity to 8.8.8.8 from VM doesn`t "
                            "function properly."),
                        'public connectivity checking from VM', ip_address)
