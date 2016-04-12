# Copyright 2016 Mirantis, Inc.
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
from fuel_health import nmanager

LOG = logging.getLogger(__name__)


class TestDPDK(neutronmanager.NeutronBaseTest, nmanager.SmokeChecksTest):
    """Test suite verifies:
    - blah-blah
    """

    def test_check_dpdk_instance_connectivity(self):
        """Check network connectivity from instance with DPDK via floating IP
        Target component: Neutron

        Scenario:
            1. Create a new security group (if it doesn`t exist yet).
            2. Create router
            3. Create network
            4. Create subnet
            5. Uplink subnet to router.
            6. Create new flavor with huge pages
            7. Create aggregate
            8. Create an instance using the new flavor, security group
               in created subnet. Boot it on compute with enabled DPDK.
            9. Create a new floating IP
            10. Assign the new floating IP to the instance.
            11. Check connectivity to the floating IP using ping command.
            12. Check that public IP 8.8.8.8 can be pinged from instance.
            13. Disassociate server floating ip.
            14. Delete floating ip
            15. Delete server.
            16. Delete aggregate
            17. Delete flavor
            18. Remove router.
            19. Remove subnet
            20. Remove network
        Duration: 300 s.

        Deployment tags: neutron dpdk
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

        name = rand_name('ost1_test-server-dpdk-')
        security_groups = [self.security_groups[self.tenant_id].name]

        router = self.verify(30, self.create_router, 2,
                             'Router can not be created', 'Router creation',
                             name)

        network = self.verify(20, self.create_network, 3,
                              'Network can not be created',
                              'Network creation', name)

        subnet = self.verify(20, self.create_subnet, 4,
                             'Subnet can not be created',
                             'Subnet creation', network)

        self.verify(20, self.uplink_subnet_to_router, 5,
                    'Can not uplink subnet to router',
                    'Uplink subnet to router', router, subnet)

        fail_msg = "Flavor was not created properly."
        flavor = self.verify(30, self._create_flavors, 6,
                             fail_msg,
                             "flavor creation",
                             self.compute_client, 255, 1, use_huge_page=True)

        fail_msg = "Aggregate was not created properly."
        aggregate = self.verify(30, self._create_aggregate, 7,
                             fail_msg,
                             "aggregate creation",
                             self.compute_client, 'nova', True)

        server = self.verify(200, self._create_server, 8,
                             "Server can not be created.",
                             "server creation",
                             self.compute_client, name, security_groups,
                             net_id=network['id'], flavor_id=flavor)

        floating_ip = self.verify(
            20,
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

        self.verify(600, self._check_connectivity_from_vm,
                    12, ("Connectivity to 8.8.8.8 from the VM doesn`t "
                         "function properly."),
                    'public connectivity checking from VM', ip_address,
                    30, (9, 60))

        self.verify(20, self.compute_client.servers.remove_floating_ip,
                    13, "Floating IP cannot be removed.",
                    "removing floating IP", server, floating_ip)

        self.verify(20, self.compute_client.floating_ips.delete,
                    14, "Floating IP cannot be deleted.",
                    "floating IP deletion", floating_ip)

        if self.floating_ips:
            self.floating_ips.remove(floating_ip)

        self.verify(40, self._delete_server, 15,
                    "Server can not be deleted. ",
                    "server deletion", server)

        self.verify(40, self._delete_aggregate, 16,
                    "Aggregate can not be deleted. ",
                    "aggregate deletion", self.compute_client, aggregate)

        self.verify(30, self._delete_flavors, 17, "Flavor failed to be deleted.",
                    "flavor deletion", self.compute_client, flavor)

        self.verify(40, self._remove_router, 18, "Router can not be deleted",
                    "router deletion", router, [subnet['id']])
        self.verify(20, self._remove_subnet, 19, "Subnet can not be deleted",
                    "Subnet deletion", subnet)
        self.verify(20, self._remove_network, 20,
                    "Network can not be deleted", "Network deletion", network)