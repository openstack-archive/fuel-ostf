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
            4. Create subnet
            5. Uplink subnet to router.
            6. Create an instance using the new security group
               in created subnet.
            7. Create a new floating IP
            8. Assign the new floating IP to the instance.
            9. Check connectivity to the floating IP using ping command.
            10. Check that public IP 8.8.8.8 can be pinged from instance.
            11. Disassociate server floating ip.
            12. Delete floating ip
            13. Delete server.
            14. Remove router.
            15. Remove subnet
            16. Remove network

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

        subnet = self.verify(20, self.create_subnet, 4,
                             'Subnet can not be created',
                             'Subnet creation', network)

        self.verify(20, self.uplink_subnet_to_router, 5,
                    'Can not uplink subnet to router',
                    'Uplink subnet to router', router, subnet)

        server = self.verify(200, self._create_server, 6,
                             "Server can not be created.",
                             "server creation",
                             self.compute_client, name, security_groups,
                             net_id=network['id'])

        floating_ip = self.verify(
            20,
            self._create_floating_ip,
            7,
            "Floating IP can not be created.",
            'floating IP creation')

        self.verify(20, self._assign_floating_ip_to_instance,
                    8, "Floating IP can not be assigned.",
                    'floating IP assignment',
                    self.compute_client, server, floating_ip)

        self.floating_ips.append(floating_ip)

        ip_address = floating_ip.ip
        LOG.info('is address is  {0}'.format(ip_address))
        LOG.debug(ip_address)

        self.verify(600, self._check_vm_connectivity, 9,
                    "VM connectivity doesn`t function properly.",
                    'VM connectivity checking', ip_address,
                    30, (9, 60))

        self.verify(600, self._check_connectivity_from_vm,
                    10, ("Connectivity to 8.8.8.8 from the VM doesn`t "
                         "function properly."),
                    'public connectivity checking from VM', ip_address,
                    30, (9, 60))

        self.verify(20, self.compute_client.servers.remove_floating_ip,
                    11, "Floating IP cannot be removed.",
                    "removing floating IP", server, floating_ip)

        self.verify(20, self.compute_client.floating_ips.delete,
                    12, "Floating IP cannot be deleted.",
                    "floating IP deletion", floating_ip)

        if self.floating_ips:
            self.floating_ips.remove(floating_ip)

        self.verify(40, self._delete_server, 13,
                    "Server can not be deleted. ",
                    "server deletion", server)

        self.verify(40, self._remove_router, 14, "Router can not be deleted",
                    "router deletion", router, [subnet['id']])
        self.verify(20, self._remove_subnet, 15, "Subnet can not be deleted",
                    "Subnet deletion", subnet)
        self.verify(20, self._remove_network, 16,
                    "Network can not be deleted", "Network deletion", network)

    def test_check_sriov_instance_connectivity(self):
            """Check network connectivity from SRIOV instance via floating IP
            Target component: Neutron

            Scenario:
                1. Create a new security group (if it doesn`t exist yet).
                2. Create SR-IOV port
                3. Create an instance using new security group and SR-IOV port.
                4. Create new floating IP
                5. Assign created floating IP to the instance.
                6. Check connectivity to the floating IP using ping command.
                7. Check that public IP 8.8.8.8 can be pinged from instance.
                8. Disassociate server floating ip.
                9. Delete floating ip
                10. Delete server.
                11. Delete SR-IOV port
            Duration: 300 s.

            Deployment tags: sriov
            """
            self.check_image_exists()
            if not self.security_groups:
                self.security_groups[self.tenant_id] = self.verify(
                    25, self._create_security_group, 1,
                    "Security group can not be created.",
                    'security group creation',
                    self.compute_client)

            name = rand_name('ost1_test-server-sriov-')
            security_groups = [self.security_groups[self.tenant_id].name]

            network = [net.id for net in
                       self.compute_client.networks.list()
                       if net.label == self.private_net]

            port = self.verify(
                20,
                self._create_port,
                2,
                "SRIOV port can not be created.",
                'SRIOV port creation',
                net_id=network[0], vnic_type='direct')

            server = self.verify(250, self._create_server, 3,
                                 "Server can not be created.",
                                 "server creation",
                                 self.compute_client, name, security_groups,
                                 port=port, net_id=network[0])

            floating_ip = self.verify(
                20,
                self._create_floating_ip,
                4,
                "Floating IP can not be created.",
                'floating IP creation')

            self.verify(20, self._assign_floating_ip_to_instance,
                        5, "Floating IP can not be assigned.",
                        'floating IP assignment',
                        self.compute_client, server, floating_ip)

            self.floating_ips.append(floating_ip)

            ip_address = floating_ip.ip
            LOG.info('is address is  {0}'.format(ip_address))
            LOG.debug(ip_address)

            self.verify(600, self._check_vm_connectivity, 6,
                        "VM connectivity doesn`t function properly.",
                        'VM connectivity checking', ip_address,
                        30, (9, 10))

            self.verify(600, self._check_connectivity_from_vm,
                        7, ("Connectivity to 8.8.8.8 from the VM doesn`t "
                            "function properly."),
                        'public connectivity checking from VM', ip_address,
                        30, (9, 10))

            self.verify(20, self.compute_client.servers.remove_floating_ip,
                        8, "Floating IP cannot be removed.",
                        "removing floating IP", server, floating_ip)

            self.verify(20, self.compute_client.floating_ips.delete,
                        9, "Floating IP cannot be deleted.",
                        "floating IP deletion", floating_ip)

            if self.floating_ips:
                self.floating_ips.remove(floating_ip)

            self.verify(30, self._delete_server, 10,
                        "Server can not be deleted. ",
                        "server deletion", server)

            self.verify(30, self.neutron_client.delete_port, 11,
                        "Port can not be deleted. ",
                        "port deletion", port['port']['id'])
