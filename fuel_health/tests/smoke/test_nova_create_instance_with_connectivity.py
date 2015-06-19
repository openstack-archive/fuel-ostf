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
    """Test suit verifies:
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
        self.check_clients_state()
        if not self.config.compute.compute_nodes:
            self.skipTest('There are no compute nodes')

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
        self.keypairs[self.tenant_id] = self.verify(30,
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
        self.check_image_exists()
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

    def test_008_check_public_instance_connectivity_from_instance(self):
        """Check network connectivity from instance via floating IP
        Target component: Nova

        Scenario:
            1. Create a new security group (if it doesn`t exist yet).
            2. Create an instance using the new security group.
            3. Create a new floating IP
            4. Assign the new floating IP to the instance.
            5. Check connectivity to the floating IP using ping command.
            6. Check that public IP 8.8.8.8 can be pinged from instance.
            7. Disassociate server floating ip.
            8. Delete floating ip
            9. Delete server.
        Duration: 300 s.

        Deployment tags: nova_network
        """
        self.check_image_exists()
        if not self.security_groups:
                self.security_groups[self.tenant_id] = self.verify(
                    25, self._create_security_group, 1,
                    "Security group can not be created.",
                    'security group creation',
                    self.compute_client)

        name = rand_name('ost1_test-server-smoke-')
        security_groups = [self.security_groups[self.tenant_id].name]

        server = self.verify(250, self._create_server, 2,
                             "Server can not be created.",
                             "server creation",
                             self.compute_client, name, security_groups)

        floating_ip = self.verify(
            20,
            self._create_floating_ip,
            3,
            "Floating IP can not be created.",
            'floating IP creation')

        self.verify(20, self._assign_floating_ip_to_instance,
                    4, "Floating IP can not be assigned.",
                    'floating IP assignment',
                    self.compute_client, server, floating_ip)

        self.floating_ips.append(floating_ip)

        ip_address = floating_ip.ip
        LOG.info('is address is  {0}'.format(ip_address))
        LOG.debug(ip_address)

        self.verify(600, self._check_vm_connectivity, 5,
                    "VM connectivity doesn`t function properly.",
                    'VM connectivity checking', ip_address,
                    30, (9, 60))

        self.verify(600, self._check_connectivity_from_vm,
                    6, ("Connectivity to 8.8.8.8 from the VM doesn`t "
                        "function properly."),
                    'public connectivity checking from VM', ip_address,
                    30, (9, 60))

        self.verify(20, self.compute_client.servers.remove_floating_ip,
                    7, "Floating IP cannot be removed.",
                    "removing floating IP", server, floating_ip)

        self.verify(20, self.compute_client.floating_ips.delete,
                    8, "Floating IP cannot be deleted.",
                    "floating IP deletion", floating_ip)

        if self.floating_ips:
            self.floating_ips.remove(floating_ip)

        self.verify(30, self._delete_server, 9,
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
        self.check_image_exists()
        if not self.security_groups:
            self.security_groups[self.tenant_id] = self.verify(
                25, self._create_security_group, 1,
                "Security group can not be created.",
                'security group creation', self.compute_client)

        name = rand_name('ost1_test-server-smoke-')
        security_groups = [self.security_groups[self.tenant_id].name]

        server = self.verify(
            250, self._create_server, 2,
            "Server can not be created.",
            'server creation',
            self.compute_client, name, security_groups)

        try:
            for addr in server.addresses:
                if addr.startswith('novanetwork'):
                    instance_ip = server.addresses[addr][0]['addr']
            if not self.config.compute.use_vcenter:
                compute = getattr(server, 'OS-EXT-SRV-ATTR:host')
            else:
                compute = None
        except Exception:
            LOG.debug(traceback.format_exc())
            self.fail("Step 3 failed: cannot get instance details. "
                      "Please refer to OpenStack logs for more details.")

        self.verify(600, self._check_connectivity_from_vm,
                    3, ("Connectivity to 8.8.8.8 from the VM doesn`t "
                        "function properly."),
                    'public connectivity checking from VM',
                    instance_ip, 30, (9, 30), compute)

        self.verify(30, self._delete_server, 4,
                    "Server can not be deleted. ",
                    "server deletion", server)

    def test_009_create_server_with_file(self):
        """Launch instance with file injection
        Target component: Nova

        Scenario:
            1. Create a new security group (if it doesn`t exist yet).
            2. Create an instance with injected file.
            3. Assign floating ip to instance.
            4. Check file exists on created instance.
            5. Delete floating ip.
            6. Delete instance.
        Duration: 200 s.
        Available since release: 2014.2-6.1
        """
        self.check_image_exists()
        if not self.security_groups:
            self.security_groups[self.tenant_id] = self.verify(
                25,
                self._create_security_group,
                1,
                "Security group can not be created.",
                'security group creation',
                self.compute_client)

        name = rand_name('ost1_test-server-smoke-file_inj-')
        security_groups = [self.security_groups[self.tenant_id].name]

        data_file = {"/home/cirros/server.txt": self._load_file('server.txt')}
        server = self.verify(
            300,
            self._create_server,
            2,
            "Creating instance using the new security group has failed.",
            'instance creation',
            self.compute_client, name, security_groups,  data_file=data_file
        )

        floating_ip = self.verify(
            20,
            self._create_floating_ip,
            3,
            "Floating IP can not be created.",
            'floating IP creation')

        self.verify(20, self._assign_floating_ip_to_instance,
                    3, "Floating IP can not be assigned.",
                    'floating IP assignment',
                    self.compute_client, server, floating_ip)

        self.floating_ips.append(floating_ip)

        ip_address = floating_ip.ip

        self.verify(
            600, self._run_command_from_vm,
            4, "Can not find injected file on instance.",
            'check if injected file exists', ip_address,
            30, (9, 60),
            '[ -f /home/cirros/server.txt ] && echo "True" || echo "False"')

        self.verify(20, self.compute_client.servers.remove_floating_ip,
                    5, "Floating IP cannot be removed.",
                    "removing floating IP", server, floating_ip)

        self.verify(20, self.compute_client.floating_ips.delete,
                    5, "Floating IP cannot be deleted.",
                    "floating IP deletion", floating_ip)

        if self.floating_ips:
            self.floating_ips.remove(floating_ip)

        self.verify(30, self._delete_server, 6,
                    "Server can not be deleted. ",
                    "server deletion", server)
