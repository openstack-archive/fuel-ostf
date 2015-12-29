# Copyright 2014 Mirantis, Inc.
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

import logging

from fuel_health.common.utils.data_utils import rand_name
from fuel_health import neutronmanager

LOG = logging.getLogger(__name__)


class TestNeutron(neutronmanager.NeutronBaseTest):
    """Test suite verifies:
    - router creation
    - network creation
    - subnet creation
    - opportunity to attach network to router
    - instance creation in created network
    - instance network connectivity
    """

    def test_check_neutron_objects_creation(self):
        """Check network connectivity from instance via floating IP
        Target component: Neutron

        Scenario:
            1. Create a new security group (if it doesn`t exist yet).
            2. Create router
            3. Create network
            4. Create IPv4 subnet
            5. Create IPv6 subnet
            6. Uplink IPv4 subnet to router.
            7. Uplink IPv6 subnet to router.
            8. Create an instance using the new security group
               in created subnets.
            9. Create a new floating IP
            10. Assign the new floating IP to the instance.
            11. Check connectivity to the floating IP using ping command.
            12. Check connectivity to the gateway_ip using ping6 command.
            13. Check that public IP 8.8.8.8 can be pinged from instance.
            14. Disassociate server floating ip.
            15. Delete floating ip
            16. Delete server.
            17. Remove router.
            18. Remove subnet
            19. Remove network

        Duration: 300 s.

        Deployment tags: neutron
        """
        if not self.config.compute.compute_nodes:
            self.skipTest('There are no compute nodes')

        self.check_image_exists()
        if not self.security_groups:
            self.security_groups[self.tenant_id] = self.verify(
                25, self._create_security_group, 1,
                "Security group can not be created.",
                'security group creation',
                self.compute_client)

        name = rand_name('ost1_test-server-smoke-')
        security_groups = [self.security_groups[self.tenant_id].name]

        router = self.verify(30, self.create_router, 2,
                             'Router can not be created', 'Router creation',
                             name)

        network = self.verify(20, self.create_network, 3,
                              'Network can not be created',
                              'Network creation', name)

        subnet_v4 = self.verify(20, self.create_subnet_v4, 4,
                                'Subnet v4 can not be created',
                                'Subnet creation', network)

        subnet_v6 = self.verify(20, self.create_subnet_v6, 5,
                                'Subnet v6 can not be created',
                                'Subnet creation', network)

        self.verify(20, self.uplink_subnet_to_router, 6,
                    'Can not uplink subnet v4 to router',
                    'Uplink subnet to router', router, subnet_v4)

        self.verify(20, self.uplink_subnet_to_router, 7,
                    'Can not uplink subnet v6 to router',
                    'Uplink subnet to router', router, subnet_v6)

        server = self.verify(200, self._create_server, 8,
                             "Server can not be created.",
                             "server creation",
                             self.compute_client, name, security_groups,
                             net_id=network['id'])

        floating_ip = self.verify(20,
                                  self._create_floating_ip,
                                  9,
                                  "Floating IP can not be created.",
                                  'floating IP creation')

        self.verify(20, self._assign_floating_ip_to_instance,
                    10, "Floating IP can not be assigned.",
                    'floating IP assignment',
                    self.compute_client, server, floating_ip)

        self.floating_ips.append(floating_ip)

        ip_address = floating_ip.ip
        LOG.info('is address is  {0}'.format(ip_address))
        LOG.debug(ip_address)

        self.verify(600, self._check_vm_connectivity, 11,
                    "VM connectivity doesn`t function properly.",
                    'VM connectivity checking', ip_address,
                    30, (9, 60))

        self.verify(600, self._check_vm_connectivity, 12,
                    "VM connectivity doesn`t function properly.",
                    'VM connectivity to gateway_ip checking',
                    subnet_v6["gateway_ip"],
                    30, (9, 60))

        self.verify(600, self._check_connectivity_from_vm,
                    13, ("Connectivity to 8.8.8.8 from the VM doesn`t "
                         "function properly."),
                    'public connectivity checking from VM', ip_address,
                    30, (9, 60))

        self.verify(20, self.compute_client.servers.remove_floating_ip,
                    14, "Floating IP cannot be removed.",
                    "removing floating IP", server, floating_ip)

        self.verify(20, self.compute_client.floating_ips.delete,
                    15, "Floating IP cannot be deleted.",
                    "floating IP deletion", floating_ip)

        if self.floating_ips:
            self.floating_ips.remove(floating_ip)

        self.verify(40, self._delete_server, 16,
                    "Server can not be deleted. ",
                    "server deletion", server)

        self.verify(40, self._remove_router, 17, "Router can not be deleted",
                    "router deletion", router, [subnet_v4['id']])
        self.verify(20, self._remove_subnet, 18, "Subnet can not be deleted",
                    "Subnet deletion", subnet_v4)
        self.verify(20, self._remove_network, 19,
                    "Network can not be deleted", "Network deletion", network)
