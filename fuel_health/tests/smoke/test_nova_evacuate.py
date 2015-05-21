# Copyright 2015 Mirantis, Inc.
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


class TestInstanceEvacuate(nmanager.NovaNetworkScenarioTest):
    """Test suit verifies:
     - Instance creation
     - Floating ip creation
     - Instance evacuate
     - Host power actions
    """
    @classmethod
    def setUpClass(cls):
        super(TestInstanceEvacuate, cls).setUpClass()
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
        super(TestInstanceEvacuate, self).setUp()
        self.check_clients_state()
        if not self.config.compute.compute_nodes and \
           self.config.compute.libvirt_type != 'vcenter':
            self.skipTest('There are no compute nodes')
        if len(self.config.compute.compute_nodes) < 2:
            self.skipTest('To test nova evacuate at least'
                          ' 2 compute nodes are needed')

    def tearDown(self):
        super(TestInstanceEvacuate, self).tearDown()
        if self.manager.clients_initialized:
            if self.servers:
                for server in self.servers:
                    try:
                        self._delete_server(server)
                        self.servers.remove(server)
                    except Exception:
                        LOG.debug(traceback.format_exc())
                        LOG.debug("Server was already deleted.")

    def test_instance_evacuate(self):
        """Instance evacuate
        Target component: Nova

        Scenario:
            1. Create a new security group.
            2. Create an instance using the new security group.
            3. Assign floating ip
            4. Check instance connectivity by floating ip
            5. Get instance host
            6. Shutdown node with instance
            6. Evacuate instance
            7. Check instance host
            8. Check connectivity to evacuated instance by floating ip
            9. Remove floating ip
            10. Delete instance.
            11. Power on compute

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

        name = rand_name('ost1_test-server-smoke-evacuate-')
        security_groups = [self.security_groups[self.tenant_id].name]

        server = self.verify(
            200,
            self._create_server,
            2,
            "Creating instance using the new security group has failed.",
            'image creation',
            self.compute_client, name, security_groups
        )

        floating_ip = self.verify(
            20,
            self._create_floating_ip,
            3,
            "Floating IP can not be created.",
            'floating IP creation')

        self.verify(10, self._assign_floating_ip_to_instance,
                    3, "Floating IP can not be assigned.",
                    'floating IP assignment',
                    self.compute_client, server, floating_ip)

        self.floating_ips.append(floating_ip)

        ip_address = floating_ip.ip
        LOG.info('is address is  {0}'.format(ip_address))
        LOG.debug(ip_address)

        self.verify(600, self._check_vm_connectivity, 4,
                    "VM connectivity doesn`t function properly.",
                    'VM connectivity checking', ip_address,
                    30, (6, 60))

        server_host = self.verify(
            20,
            self.get_instance_host,
            5,
            "Failed to get server host.",
            'get server host',
            self.compute_client, server
        )

        self.verify(
            200,
            self.host_power_action,
            6,
            "Turning off compute where instance is allocated has failed.",
            'shutdown host',
            self.compute_client, server_host, 'shutdown'
        )

        evacuated_server = self.verify(
            300,
            self.evacuate_instance,
            7,
            "Evacuation failed", 'Instance evacuation',
            self.compute_client, server)

        LOG.debug('Evacuated instance {0}'.format(evacuated_server))

        self.verify(600, self._check_vm_connectivity, 8,
                    "VM connectivity doesn`t function properly.",
                    'VM connectivity checking', ip_address,
                    30, (6, 60))

        self.verify(10, self.compute_client.servers.remove_floating_ip,
                    9, "Floating IP cannot be removed.",
                    "removing floating IP", evacuated_server, floating_ip)

        self.verify(10, self.compute_client.floating_ips.delete,
                    9, "Floating IP cannot be deleted.",
                    "floating IP deletion", floating_ip)

        if self.floating_ips:
            self.floating_ips.remove(floating_ip)

        self.verify(30, self._delete_server, 10,
                    "Server can not be deleted.",
                    "server deletion", server)

        self.verify(
            200,
            self.host_power_action,
            11,
            "Turning on compute host has failed.",
            'startup host',
            self.compute_client, server_host, 'startup'
        )
