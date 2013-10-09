# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
# Copyright 2013 Mirantis, Inc.
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

from fuel_health.common.ssh import Client as SSHClient

import time

from fuel_health.common.utils.data_utils import rand_name
from fuel_health import exceptions
import fuel_health.test

from fuel_health import nmanager


LOG = logging.getLogger(__name__)


class NeutronScenarioTest(nmanager.OfficialClientTest):
    """
    Base class for neutron scenario tests
    """

    @classmethod
    def check_preconditions(cls):
        cls._create_nano_flavor()
        cls._enabled = True
        if cls.config.network.network_provider != 'neutron':
            cls._enabled = False
        else:
            cls._enabled = True

    def setUp(self):
        super(NeutronScenarioTest, self).setUp()

    @classmethod
    def setUpClass(cls):
        super(NeutronScenarioTest, cls).setUpClass()
        cls.host = cls.config.compute.controller_nodes
        cls.usr = cls.config.compute.controller_node_ssh_user
        cls.pwd = cls.config.compute.controller_node_ssh_password
        cls.key = cls.config.compute.path_to_private_key
        cls.timeout = cls.config.compute.ssh_timeout
        cls.tenant_id = cls.manager._get_identity_client(
            cls.config.identity.admin_username,
            cls.config.identity.admin_password,
            cls.config.identity.admin_tenant_name).tenant_id
        cls.network = []
        cls.subnet = []
        cls.floating_ips = []
        cls.sec_group = []
        cls.error_msg = []
        cls.tenants = []
        cls.users = []

    def _create_keypair(self, client, namestart='ost1_test-keypair-smoke-'):
        kp_name = rand_name(namestart)
        keypair = client.keypairs.create(kp_name)
        self.set_resource(kp_name, keypair)
        self.verify_response_body_content(keypair.id,
                                          kp_name,
                                          'Keypair creation failed')
        return keypair

    def _create_tenant(self):
        name = rand_name('ost1_test-tenant-')
        tenant = self.identity_client.tenants.create(name)
        self.tenants.append(tenant)
        return tenant

    @classmethod
    def _clean_tenants(cls):
        if cls.tenants:
            for ten in cls.tenants:
                try:
                    cls.identity_client.tenants.delete(ten)
                except Exception as exc:
                    cls.error_msg.append(exc)
                    LOG.debug(exc)
                    pass

    def _create_user(self, client, tenant_id):
        password = "123456"
        email = "test@test.com"
        name = rand_name('ost1_test-user-')
        user = client.users.create(name, password, email, tenant_id)
        self.users.append(user)
        return user

    @classmethod
    def _clean_users(cls):
        if cls.users:
            for user in cls.users:
                try:
                    cls.identity_client.users.delete(user)
                except Exception as exc:
                    cls.error_msg.append(exc)
                    LOG.debug(exc)
                    pass

    def _create_security_group(
            self, namestart='ost1_test-secgroup-smoke-netw'):
        # Create security group
        sg_name = rand_name(namestart)
        sg_desc = sg_name + " description"
        secgroup = self.network_client.create_security_group(
            {'name': sg_name, 'description': sg_desc})
        self.set_resource(sg_name, secgroup)
        self.verify_response_body_content(secgroup.name,
                                          sg_name,
                                          "Security group creation failed")
        self.verify_response_body_content(secgroup.description,
                                          sg_desc,
                                          "Security group creation failed")

        # Add rules to the security group

        # These rules are intended to permit inbound ssh and icmp
        # traffic from all sources, so no group_id is provided.
        # Setting a group_id would only permit traffic from ports
        # belonging to the same security group.
        rulesets = [
            {
                # ssh
                'ip_protocol': 'tcp',
                'from_port': 22,
                'to_port': 22,
                'cidr': '0.0.0.0/0',
            },
            {
                # ping
                'ip_protocol': 'icmp',
                'from_port': -1,
                'to_port': -1,
                'cidr': '0.0.0.0/0',
            }
        ]
        for ruleset in rulesets:
            try:
                self.network_client.create_security_group_rule(
                    body=ruleset)
            except Exception:
                self.fail("Failed to create rule in security group.")

        return secgroup

    def _create_network(self, tenant_id, label='ost1_test-network-smoke-'):
        n_label = rand_name(label)
        network = {"admin_state_up": True,
                   "name": n_label,
                   #'Shared' maybe also required.
                   "tenant_id": tenant_id}
        networks = self.network_client.create_network(network)['body']
        self.set_resource(n_label, networks)
        self.network.append(networks)
        self.verify_response_body_content(networks.label,
                                          n_label,
                                          "Network creation failed")
        return networks

    @classmethod
    def _clear_networks(cls):
        try:
            for net in cls.network:
                cls.network_client.delete_network(net['id'])
        except Exception as exc:
            cls.error_msg.append(exc)
            LOG.debug(exc)
            pass

    def _create_subnet(self, network):
        tenant_id = network['tenant_id']
        subnet = {"network_id": network['id'],
                  "tenant_id": tenant_id,
                  "ip_version": 4,
                  "cidr": self.config.network.cidr}

        subnet = self.network_client.create_subnet(subnet)
        self.subnet.append(subnet)
        return subnet

    def _list_networks(self):
        return self.network_client.list_networks()['networks']

    def _list_subnets(self):
        return self.network_client.list_subnets()['subnets']

    def _list_routers(self):
        return self.network_client.list_routers()['routers']

    def _create_server(self, client, name, security_groups, network):
        base_image_id = nmanager.get_image_from_name()
        create_kwargs = {
            'security_groups': security_groups,
            'nics': [{'net-id': network.id}]
        }
        self._create_nano_flavor()
        server = client.servers.create(name, base_image_id, 42,
                                       **create_kwargs)
        self.verify_response_body_content(server.name,
                                          name,
                                          "Instance creation failed")
        self.set_resource(name, server)
        self.status_timeout(client.servers, server.id, 'ACTIVE')
        # The instance retrieved on creation is missing network
        # details, necessitating retrieval after it becomes active to
        # ensure correct details.
        server = client.servers.get(server.id)
        self.set_resource(name, server)
        return server

    def _create_floating_ip(self, server):
        result = self.network_client.list_ports(device_id=server.id)
        ports = result.get('ports', [])
        self.verify_response_body_content(len(ports), 1,
                                          ("Unable to determine "
                                           "which port to target."))
        network = self._get_router(
            self.tenant_id)['routers']["external_gateway_info"]["network_id"]


        data = {'floating_network_id': network.id}
        floating_ip = self.network_client.create_floatingip(
            body=data)['floating_ip']

        self.floating_ips.append(floating_ip)
        return floating_ip

    def _assign_floating_ip_to_instance(self, client, server, floating_ip):
        try:
            client.servers.add_floating_ip(server, floating_ip)
        except Exception:
            self.fail('Can not assign floating ip to instance')

    @classmethod
    def _clean_floating_ips(cls):
        for ip in cls.floating_ips:
            try:
                cls.network_client.delete_floatingip(ip)
            except Exception as exc:
                cls.error_msg.append(exc)
                LOG.debug(exc)
                pass

    def _ping_ip_address(self, ip_address):
        def ping():
            cmd = 'ping -c1 -w1 ' + ip_address
            time.sleep(30)

            if self.host:

                try:
                    SSHClient(self.host[0],
                              self.usr, self.pwd,
                              key_filename=self.key,
                              timeout=self.timeout).exec_command(cmd)
                    return True

                # except SSHExecCommandFailed as exc:
                #     output_msg = "Instance is not reachable by floating IP."
                #     LOG.debug(exc)
                #     self.fail(output_msg)
                except Exception as exc:
                    LOG.debug(exc)
                    self.fail("Connection failed.")

            else:
                self.fail('Wrong tests configurations, one from the next '
                          'parameters are empty controller_node_name or '
                          'controller_node_ip ')
        # TODO Allow configuration of execution and sleep duration.
        return fuel_health.test.call_until_true(ping, 40, 1)

    def _ping_ip_address_from_instance(self, ip_address, viaHost=None,
                                       to_ping='8.8.8.8'):
        def ping():
            time.sleep(30)
            ssh_timeout = self.timeout > 30 and self.timeout or 30
            if not (self.host or viaHost):
                self.fail('Wrong tests configurations, one from the next '
                          'parameters are empty controller_node_name or '
                          'controller_node_ip ')

            host = viaHost or self.host[0]
            ssh = SSHClient(host,
                            self.usr, self.pwd,
                            key_filename=self.key,
                            timeout=ssh_timeout)
            LOG.debug('Get ssh to auxiliary host')
            ssh.exec_command_on_vm(
                command='ping -c1 -w1 {ip}'.format(ip=to_ping),
                user='cirros',
                password='cubswin:)',
                vm=ip_address)
            LOG.debug('Get ssh to instance')
            return True
            # except SSHExecCommandFailed as exc:
            #     LOG.debug(exc)
            #     return False
                # self.fail(output_msg)

        #  TODO Allow configuration of execution and sleep duration.
        return fuel_health.test.call_until_true(ping, 40, 1)

    def _check_vm_connectivity(self, ip_address):
        self.assertTrue(self._ping_ip_address(ip_address),
                        "Timed out waiting for %s to become "
                        "reachable. Please, check Network "
                        "configuration" % ip_address)

    def _check_connectivity_from_vm(self, ip_address, viaHost=None,
                                    to_ping='8.8.8.8'):
        self.assertTrue(self._ping_ip_address_from_instance(ip_address,
                                                            viaHost=viaHost,
                                                            to_ping=to_ping),
                        "Timed out waiting for %s to become "
                        "reachable. Please, check Network "
                        "configuration" % ip_address)

    @classmethod
    def _verification_of_exceptions(cls):
        if cls.error_msg:
            for err in cls.error_msg:
                if err.__class__.__name__ == 'InternalServerError':
                    raise cls.failureException('REST API of '
                                               'OpenStack is inaccessible.'
                                               ' Please try again')
                if err.__class__.__name__ == 'ClientException':
                    raise cls.failureException('REST API of '
                                               'OpenStack is inaccessible.'
                                               ' Please try again')

    def _get_router(self, tenant_id):
        """Retrieve a router for the given tenant id.

        If a public router has been configured, it will be returned.

        If a public router has not been configured, but a public
        network has, a tenant router will be created and returned that
        routes traffic to the public network.

        """
        router_id = self.config.network.public_router_id
        network_id = self.config.network.public_network_id
        if router_id:
            result = self.network_client.show_router(router_id)
            return result['body']
        elif network_id:
            router = self._create_router(tenant_id)
            router.add_gateway(network_id)
            return router
        else:
            raise Exception("Neither of 'public_router_id' or "
                            "'public_network_id' has been defined.")

    def _add_interface_to_router(self, router, subnet_id):
        self.network_client.add_interface_router(router,
                                                 {'subnet_id': subnet_id})

    @classmethod
    def tearDownClass(cls):
        super(NeutronScenarioTest, cls).tearDownClass()
        cls._clean_floating_ips()
        cls._clear_networks()
        cls._clean_users()
        cls._clean_tenants()
        cls._verification_of_exceptions()