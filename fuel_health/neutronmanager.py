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
import traceback

import fuel_health.nmanager

LOG = logging.getLogger(__name__)


class NeutronBaseTest(fuel_health.nmanager.NovaNetworkScenarioTest):

    @classmethod
    def setUpClass(cls):
        super(NeutronBaseTest, cls).setUpClass()
        cls.tenant_id = cls.identity_client().tenant_id
        cls.routers = {}
        cls.subnets = []
        cls.networks = []

    def setUp(self):
        super(NeutronBaseTest, self).setUp()
        self.check_clients_state()
        if not self.neutron_client:
            self.skipTest('Neutron is unavailable.')

    def create_router(self, name):
        external_network = None
        for network in self.neutron_client.list_networks()["networks"]:
            if network.get("router:external"):
                external_network = network

        if not external_network:
            self.fail('Can not find external network')

        gw_info = {
            "network_id": external_network["id"],
            "enable_snat": True
        }

        router_info = {
            "router": {
                "name": name,
                "external_gateway_info": gw_info,
                "tenant_id": self.tenant_id
            }
        }

        router = self.neutron_client.create_router(router_info)['router']
        self.routers.setdefault(router['id'], [])

        return router

    def create_network(self, name):
        internal_network_info = {
            "network": {
                "name": name,
                "tenant_id": self.tenant_id
            }
        }

        network = self.neutron_client.create_network(
            internal_network_info)['network']
        self.networks.append(network)

        return network

    def create_subnet(self, internal_network):
        subnet_info = {
            "subnet": {
                "network_id": internal_network['id'],
                "ip_version": 4,
                "cidr": "10.0.7.0/24",
                "tenant_id": self.tenant_id
            }
        }

        subnet = self.neutron_client.create_subnet(subnet_info)['subnet']
        self.subnets.append(subnet)

        return subnet

    def uplink_subnet_to_router(self, router, subnet):
        if not self.routers.get(router['id'], None):
            self.routers[router['id']].append(subnet['id'])

        return self.neutron_client.add_interface_router(
            router["id"], {"subnet_id": subnet["id"]})

    def _remove_router(self, router, subnets_id=[]):
        self.neutron_client.remove_gateway_router(router['id'])

        for subnet_id in subnets_id:
            self.neutron_client.remove_interface_router(
                router['id'], {"subnet_id": subnet_id})

        self.neutron_client.delete_router(router['id'])

    def _remove_subnet(self, subnet):
        return self.neutron_client.delete_subnet(subnet['id'])

    def _remove_network(self, network):
        self.neutron_client.delete_network(network['id'])

    @classmethod
    def _clear_networks(cls):
        try:
            for router in cls.routers:
                cls._remove_router(router, cls.routers[router])
        except Exception as exc:
            cls.error_msg.append(exc)
            LOG.debug(traceback.format_exc())

        try:
            for subnet in cls.subnets:
                cls._remove_subnet(subnet)
        except Exception as exc:
            cls.error_msg.append(exc)
            LOG.debug(traceback.format_exc())

        try:
            for network in cls.networks:
                cls._remove_network(network)
        except Exception as exc:
            cls.error_msg.append(exc)
            LOG.debug(traceback.format_exc())
