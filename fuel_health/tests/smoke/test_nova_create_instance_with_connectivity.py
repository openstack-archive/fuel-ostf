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
from nose.tools import timed

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
    @timed(25)
    def test_001_create_keypairs(self):
        """Keypair creation
        Target component: Nova.

        Scenario:
            1. Create a new keypair, check if it was created successfully.
        Duration: 10-25 s.
        """
        try:
            self.keypairs[self.tenant_id] = self._create_keypair(
                self.compute_client)
        except Exception as e:
            LOG.error("Keypair creation failed: %s" % e)
            self.fail("Step 1 failed: Create keypair.")

    @attr(type=['fuel', 'smoke'])
    @timed(25)
    def test_002_create_security_groups(self):
        """Security group creation
        Target component: Nova

        Scenario:
            1. Create security group, check if it was created correctly.
        Duration: 2-25 s.
        """
        try:
            self.security_groups[self.tenant_id] = self._create_security_group(
                self.compute_client)
        except Exception as e:
            LOG.error("Security group creation failed: %s" % e)
            self.fail("Step 1 failed: Create security group.")

    @attr(type=['fuel', 'smoke'])
    @timed(50)
    def test_004_check_networks(self):
        """Network parameters check
        Target component: Nova

        Scenario:
            1. Get list of networks.
            2. Check seen network labels equal to expected ones.
            3. Check seen network ids equal to expected ones.
        Duration: 1-50 s.
        """
        try:
            seen_nets = self._list_networks()
        except Exception as e:
            LOG.error("Getting network list failed: %s" % e)
            self.fail("Step 1 failed: Get list of networks.")
        seen_labels = [n.label for n in seen_nets]
        seen_ids = [n.id for n in seen_nets]
        for mynet in self.network:
            self.verify_response_body(seen_labels,
                                      mynet.label,
                                      ('Network is not created '
                                       'properly'),
                                      failed_step=2)
            self.verify_response_body(seen_ids,
                                      mynet.id,
                                      ('Network is not created'
                                       ' properly '),
                                      failed_step=3)

    @attr(type=['fuel', 'smoke'])
    @timed(150)
    def test_005_create_servers(self):
        """Instance creation
        Target component: Nova

        Scenario:
            1. Create new keypair (if it`s nonexistent yet).
            2. Create new sec group (if it`s nonexistent yet).
            3. Create instance with usage of created sec group and keypair.
        Duration: 50-150 s.
        """
        if not self.keypairs:
            try:
                self.keypairs[self.tenant_id] = self._create_keypair(
                    self.compute_client)
            except Exception as e:
                LOG.error("Keypair creation failed: %s" % e)
                self.fail("Step 1 failed: Necessary resources for "
                          "booting instance"
                          " has not been created")
        if not self.security_groups:
            try:
                self.security_groups[self.tenant_id] = \
                    self._create_security_group(self.compute_client)
            except Exception as e:
                LOG.error("Security group creation failed: %s" % e)
                self.fail("Step 2 failed: Necessary resources for"
                          " booting instance"
                          " has not been created")

        name = rand_name('ost1_test-server-smoke-')
        keypair_name = self.keypairs[self.tenant_id].name
        security_groups = [self.security_groups[self.tenant_id].name]

        try:
            server = self._create_server(self.compute_client,
                                         name, keypair_name, security_groups)
        except Exception as e:
            LOG.error("Server creation failed: %s" % e)
            self.fail("Step 3: create instance with usage of created "
                      "security group and keypair failed.")
        self.servers.append(server)

    @attr(type=['fuel', 'smoke'])
    @timed(55)
    def test_007_assign_floating_ips(self):
        """Floating IP assignment
        Target component: Nova

        Scenario:
            1. Create new keypair (if it`s nonexistent yet).
            2. Create new sec group (if it`s nonexistent yet).
            3. Create instance with usage of created sec group and keypair.
            4. Create new floating ip.
            5. Assign floating ip to created instance.
        Duration: 40-55 s.
        """
        if not self.servers:
            if not self.keypairs:
                try:
                    self.keypairs[self.tenant_id] = self._create_keypair(
                        self.compute_client)
                except Exception as e:
                    LOG.error("Keypair creation failed: %s" % e)
                    self.fail("Step 1 failed: Necessary resources "
                              "for booting instance"
                              " has not been created.")
            if not self.security_groups:
                try:
                    self.security_groups[self.tenant_id] = self.\
                        _create_security_group(self.compute_client)
                except Exception as e:
                    LOG.error("Security group creation failed: %s" % e)
                    self.fail("Step 2 failed: Necessary resources "
                              "for booting instance"
                              " has not been created.")

            name = rand_name('ost1_test-server-smoke-')
            keypair_name = self.keypairs[self.tenant_id].name
            security_groups = [self.security_groups[self.tenant_id].name]

            try:
                server = self._create_server(self.compute_client,
                            name, keypair_name, security_groups)
            except Exception as e:
                LOG.error("Server creation failed: %s" % e)
                self.fail("Step 3 failed: Create server.")
            self.servers.append(server)
            try:
                floating_ip = self._create_floating_ip()
            except Exception as e:
                LOG.error("Floating IP creation failed. %s" % e)
                self.fail("Step 4 failed: Create floating IP.")

            try:
                self._assign_floating_ip_to_instance(
                    self.compute_client, server, floating_ip)
            except Exception as e:
                LOG.error("Floating IP assignment failed: %s" % e)
                self.fail("Step 5 failed: Assign floating "
                          "IP to an instance.")
            self.floating_ips.append(floating_ip)

    @attr(type=['fuel', 'smoke'])
    @timed(55)
    def test_008_check_public_network_connectivity(self):
        """Network connectivity check through floating ip.
        Target component: Nova

        Scenario:
            1. Create new keypair (if it`s nonexistent yet).
            2. Create new sec group (if it`s nonexistent yet).
            3. Create instance with usage of created sec group and keypair.
            4. Check connectivity for all floating ips using ping command.
        Duration: 40-55 s.
        """
        if not self.floating_ips:
            if not self.servers:
                if not self.keypairs:
                    try:
                        self.keypairs[self.tenant_id] = self._create_keypair(
                            self.compute_client)
                    except Exception as e:
                        LOG.debug("Keypair creation failed: %s" % e)
                        self.fail("Step 1 failed: Necessary resources"
                                  " for booting instance"
                                  " has not been created.")
                if not self.security_groups:
                    try:
                        self.security_groups[self.tenant_id] = self.\
                            _create_security_group(self.compute_client)
                    except Exception as e:
                        LOG.debug("Security group creation failed: %s" % e)
                        self.fail("Step 2 failed: Necessary resources "
                                  "for booting instance"
                                  " has not been created.")

                name = rand_name('ost1_test-server-smoke-')
                keypair_name = self.keypairs[self.tenant_id].name
                security_groups = [self.security_groups[self.tenant_id].name]

                try:
                    server = self._create_server(
                        self.compute_client, name, keypair_name,
                        security_groups)
                    self.servers.append(server)
                except Exception as e:
                    LOG.debug("Server creation failed: %s" % e)
                    self.fail("Step 3 failed: create server.")
            for server in self.servers:
                try:
                    floating_ip = self._create_floating_ip()
                except Exception as e:
                    LOG.debug("Floating IP creation failed. %s" % e)
                    self.fail("Step 4 failed: Create floating IP.")
                try:
                    self._assign_floating_ip_to_instance(
                        self.compute_client, server, floating_ip)
                    self.floating_ips.append(floating_ip)
                except Exception as e:
                    LOG.debug("Floating IP assignment failed: %s" % e)
                    self.fail("Step 5 failed: Assign floating IP "
                              "to an instance.")

        # The target login is assumed to have been configured for
        # key-based authentication by cloud-init.
        ssh_login = self.config.compute.image_ssh_user
        private_key = self.keypairs[self.tenant_id].private_key
        try:
            for floating_ip in self.floating_ips:
                ip_address = floating_ip.ip
                self._check_vm_connectivity(ip_address, ssh_login, private_key)
        except Exception as e:
            LOG.debug("VM connectivity check failed: %s" % e)
            self.fail("Step 6 failed: Check VM connectivity.")
