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


class TestNeutronIPv6(neutronmanager.NeutronBaseTest):
    """Test suite verifies:
    - router creation
    - network creation
    - subnet creation
    - opportunity to attach network to router
    - instance creation in created network
    - instance network connectivity via IPv6
    """

    def test_check_neutron_ipv6_connectivity(self):
        """Check network connectivity between instances via IPv6
        Target component: Neutron IPv6 support

        Scenario:
            1. Create a new security group (if it doesn`t exist yet).
            2. Create router
            3. Create 1 network (for server1)
            4. Create 2 network (for server2)
            5. Create IPv4 subnet(for server1)
            6. Create IPv6 subnet (for server1)
            7. Create IPv4 subnet (for server2)
            8. Create IPv6 subnet (for server2)
            9. Uplink IPv4 subnet1 to router.
            10. Uplink IPv4 subnet2 to router.
            11. Uplink IPv6 subnet1 to router.
            12. Uplink IPv6 subnet2 to router.
            13. Create a master instance using the new security group
                in created network 1.
            14. Create a slave instance using the new security group
                in created network 2.
            15. Create a new floating IP (server1)
            16. Create a new floating IP (server2)
            17. Assign the new floating IP to the master instance.
            18. Assign the new floating IP to the slave instance.
            19. Check connectivity to the master instance using ping command.
            20. Check connectivity to the slave instance using ping command.
            21. Check connectivity between instances using ping6 command.
            22. Disassociate server1 floating ip.
            23. Disassociate server2 floating ip.
            24. Delete floating ip 1
            25. Delete floating ip 2
            26. Delete master server.
            27. Delete slave server.
            28. Remove router.
            29. Remove master v4 subnet
            30. Remove master v6 subnet
            31. Remove slave v4 subnet
            32. Remove slave v6 subnet
            33. Remove network 1
            34. Remove network 2

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

        name1 = rand_name('ost1_test-server1-smoke-')
        name2 = rand_name('ost1_test-server2-smoke-')
        security_groups = [self.security_groups[self.tenant_id].name]

        router = self.verify(30, self.create_router, 2,
                             'Router can not be created', 'Router creation',
                             name1)

        network1 = self.verify(20, self.create_network, 3,
                               'Network can not be created',
                               'Network creation', name1)

        network2 = self.verify(20, self.create_network, 4,
                               'Network can not be created',
                               'Network creation', name2)

        subnet_1_v4 = self.verify(20, self.create_subnet_v4, 5,
                                  'Subnet v4 can not be created',
                                  'Subnet creation',
                                  network1, '192.168.100.0/24')

        subnet_1_v6 = self.verify(20, self.create_subnet_v6, 6,
                                  'Subnet v6 can not be created',
                                  'Subnet creation',
                                  network1,
                                  "2001:db8:100::/64", "2001:db8:100::1")

        subnet_2_v4 = self.verify(20, self.create_subnet_v4, 7,
                                  'Subnet v4 can not be created',
                                  'Subnet creation',
                                  network2, '192.168.200.0/24')

        subnet_2_v6 = self.verify(20, self.create_subnet_v6, 8,
                                  'Subnet v6 can not be created',
                                  'Subnet creation',
                                  network2,
                                  "2001:db8:200::/64", "2001:db8:200::1")

        self.verify(20, self.uplink_subnet_to_router, 9,
                    'Can not uplink subnet v4 to router',
                    'Uplink subnet to router', router, subnet_1_v4)

        self.verify(20, self.uplink_subnet_to_router, 10,
                    'Can not uplink subnet v4 to router',
                    'Uplink subnet to router', router, subnet_2_v4)

        self.verify(20, self.uplink_subnet_to_router, 11,
                    'Can not uplink subnet v6 to router',
                    'Uplink subnet to router', router, subnet_1_v6)

        self.verify(20, self.uplink_subnet_to_router, 12,
                    'Can not uplink subnet v6 to router',
                    'Uplink subnet to router', router, subnet_2_v6)

        server1 = self.verify(200, self._create_server, 13,
                              "Server can not be created.",
                              "server creation",
                              self.compute_client, name1, security_groups,
                              net_id=network1['id'])

        server2 = self.verify(200, self._create_server, 14,
                              "Server can not be created.",
                              "server creation",
                              self.compute_client, name2, security_groups,
                              net_id=network2['id'])

        floating_ip1 = self.verify(20,
                                   self._create_floating_ip,
                                   15,
                                   "Floating IP can not be created.",
                                   'floating IP creation')

        floating_ip2 = self.verify(20,
                                   self._create_floating_ip,
                                   16,
                                   "Floating IP can not be created.",
                                   'floating IP creation')

        self.verify(20, self._assign_floating_ip_to_instance,
                    17, "Floating IP can not be assigned.",
                    'floating IP assignment',
                    self.compute_client, server1, floating_ip1)

        self.verify(20, self._assign_floating_ip_to_instance,
                    18, "Floating IP can not be assigned.",
                    'floating IP assignment',
                    self.compute_client, server2, floating_ip2)

        self.floating_ips.append(floating_ip1)
        self.floating_ips.append(floating_ip2)

        master_ipv6 = [
            addr['addr'] for addr in server1.addresses[network1['name']]
            if addr['version'] == 6
        ].pop()

        slave_ipv6 = [
            addr['addr'] for addr in server2.addresses[network2['name']]
            if addr['version'] == 6
        ].pop()

        LOG.info('master floating IP address is {0}'.format(floating_ip1.ip))
        LOG.info('master IPv6 address is {0}'.format(master_ipv6))
        LOG.info('slave floating IP address is {0}'.format(floating_ip2.ip))
        LOG.info('slave IPv6 address is {0}'.format(slave_ipv6))

        self.verify(600, self._check_vm_connectivity, 19,
                    "VM connectivity doesn`t function properly.",
                    'VM connectivity checking', floating_ip1.ip,
                    30, (9, 60))

        self.verify(600, self._check_vm_connectivity, 20,
                    "VM connectivity doesn`t function properly.",
                    'VM connectivity checking', floating_ip2.ip,
                    30, (9, 60))

        self.verify(600, self._check_connectivity_from_vm, 21,
                    "Connectivity to the slave VM from the master VM via IPv6 "
                    "doesn`t function properly.",
                    "Connectivity checking to the slave VM from the master VM "
                    "via IPv6",
                    floating_ip1.ip, 30, (9, 60), slave_ipv6)

        self.verify(20, self.compute_client.servers.remove_floating_ip,
                    22, "Floating IP cannot be removed.",
                    "removing floating IP", server1, floating_ip1)

        self.verify(20, self.compute_client.servers.remove_floating_ip,
                    23, "Floating IP cannot be removed.",
                    "removing floating IP", server2, floating_ip2)

        self.verify(20, self.compute_client.floating_ips.delete,
                    24, "Floating IP cannot be deleted.",
                    "floating IP deletion", floating_ip1)

        if floating_ip1 in self.floating_ips:
            self.floating_ips.remove(floating_ip1)

        self.verify(20, self.compute_client.floating_ips.delete,
                    25, "Floating IP cannot be deleted.",
                    "floating IP deletion", floating_ip2)

        if floating_ip2 in self.floating_ips:
            self.floating_ips.remove(floating_ip2)

        self.verify(40, self._delete_server, 26,
                    "Server can not be deleted. ",
                    "server deletion", server1)

        self.verify(40, self._delete_server, 27,
                    "Server can not be deleted. ",
                    "server deletion", server2)

        self.verify(40, self._remove_router, 28, "Router can not be deleted",
                    "router deletion",
                    router,
                    [
                        subnet_1_v4['id'], subnet_1_v6['id'],
                        subnet_2_v4['id'], subnet_2_v6['id']
                    ])

        self.verify(20, self._remove_subnet, 29,
                    "Subnet v4 can not be deleted",
                    "Subnet v4 deletion", subnet_1_v4)
        self.verify(20, self._remove_subnet, 30,
                    "Subnet v6 can not be deleted",
                    "Subnet v6 deletion", subnet_1_v6)
        self.verify(20, self._remove_subnet, 31,
                    "Subnet v4 can not be deleted",
                    "Subnet v4 deletion", subnet_2_v4)
        self.verify(20, self._remove_subnet, 32,
                    "Subnet v6 can not be deleted",
                    "Subnet v6 deletion", subnet_2_v6)
        self.verify(20, self._remove_network, 33,
                    "Network can not be deleted", "Network deletion", network1)
        self.verify(20, self._remove_network, 34,
                    "Network can not be deleted", "Network deletion", network2)
