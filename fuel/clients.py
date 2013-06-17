# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

from fuel.common import log as logging
from fuel import config
from fuel import exceptions
from fuel.services.compute.json.fixed_ips_client import FixedIPsClientJSON
from fuel.services.compute.json.flavors_client import FlavorsClientJSON
from fuel.services.compute.json.floating_ips_client import \
    FloatingIPsClientJSON
from fuel.services.compute.json.hosts_client import HostsClientJSON
from fuel.services.compute.json.hypervisor_client import \
    HypervisorClientJSON
from fuel.services.compute.json.images_client import ImagesClientJSON
from fuel.services.compute.json.interfaces_client import \
    InterfacesClientJSON
from fuel.services.compute.json.keypairs_client import KeyPairsClientJSON
from fuel.services.compute.json.limits_client import LimitsClientJSON
from fuel.services.compute.json.quotas_client import QuotasClientJSON
from fuel.services.compute.json.security_groups_client import \
    SecurityGroupsClientJSON
from fuel.services.compute.json.servers_client import ServersClientJSON
from fuel.services.compute.json.services_client import ServicesClientJSON
from fuel.services.compute.json.tenant_usages_client import \
    TenantUsagesClientJSON
from fuel.services.identity.json.identity_client import IdentityClientJSON
from fuel.services.identity.json.identity_client import TokenClientJSON
from fuel.services.network.json.network_client import NetworkClient

from fuel.services.volume.json.admin.volume_types_client import \
    VolumeTypesClientJSON
from fuel.services.volume.json.snapshots_client import SnapshotsClientJSON
from fuel.services.volume.json.volumes_client import VolumesClientJSON


LOG = logging.getLogger(__name__)

IMAGES_CLIENTS = {
    "json": ImagesClientJSON,
    }

KEYPAIRS_CLIENTS = {
    "json": KeyPairsClientJSON,
}

QUOTAS_CLIENTS = {
    "json": QuotasClientJSON,
}

SERVERS_CLIENTS = {
    "json": ServersClientJSON,
}

LIMITS_CLIENTS = {
    "json": LimitsClientJSON,
}

FLAVORS_CLIENTS = {
    "json": FlavorsClientJSON,
}

FLOAT_CLIENTS = {
    "json": FloatingIPsClientJSON,
}

SNAPSHOTS_CLIENTS = {
    "json": SnapshotsClientJSON,
}

VOLUMES_CLIENTS = {
    "json": VolumesClientJSON,
}

VOLUME_TYPES_CLIENTS = {
    "json": VolumeTypesClientJSON,
}

IDENTITY_CLIENT = {
    "json": IdentityClientJSON,
}

TOKEN_CLIENT = {
    "json": TokenClientJSON,
}

SECURITY_GROUPS_CLIENT = {
    "json": SecurityGroupsClientJSON,
}

INTERFACES_CLIENT = {
    "json": InterfacesClientJSON,
}

FIXED_IPS_CLIENT = {
    "json": FixedIPsClientJSON,
}

SERVICES_CLIENT = {
    "json": ServicesClientJSON,
}

TENANT_USAGES_CLIENT = {
    "json": TenantUsagesClientJSON,
}

HYPERVISOR_CLIENT = {
    "json": HypervisorClientJSON,
}


class Manager(object):

    """
    Top level manager for OpenStack Compute clients
    """

    def __init__(self, username=None, password=None, tenant_name=None,
                 interface='json'):
        """
        We allow overriding of the credentials used within the various
        client classes managed by the Manager object. Left as None, the
        standard username/password/tenant_name is used.

        :param username: Override of the username
        :param password: Override of the password
        :param tenant_name: Override of the tenant name
        """
        self.config = config.FuelConfig()

        # If no creds are provided, we fall back on the defaults
        # in the config file for the Compute API.
        self.username = username or self.config.identity.username
        self.password = password or self.config.identity.password
        self.tenant_name = tenant_name or self.config.identity.tenant_name

        if None in (self.username, self.password, self.tenant_name):
            msg = ("Missing required credentials. "
                   "username: %(username)s, password: %(password)s, "
                   "tenant_name: %(tenant_name)s") % locals()
            raise exceptions.InvalidConfiguration(msg)

        self.auth_url = self.config.identity.uri
        self.auth_url_v3 = self.config.identity.uri_v3

        if self.config.identity.strategy == 'keystone':
            client_args = (self.config, self.username, self.password,
                           self.auth_url, self.tenant_name)

            if self.auth_url_v3:
                auth_version = 'v3'
                client_args_v3_auth = (self.config, self.username,
                                       self.password, self.auth_url_v3,
                                       self.tenant_name, auth_version)
            else:
                client_args_v3_auth = None

        else:
            client_args = (self.config, self.username, self.password,
                           self.auth_url)

            client_args_v3_auth = None

        try:
            self.servers_client = SERVERS_CLIENTS[interface](*client_args)
            self.limits_client = LIMITS_CLIENTS[interface](*client_args)
            self.images_client = IMAGES_CLIENTS[interface](*client_args)
            self.keypairs_client = KEYPAIRS_CLIENTS[interface](*client_args)
            self.quotas_client = QUOTAS_CLIENTS[interface](*client_args)
            self.flavors_client = FLAVORS_CLIENTS[interface](*client_args)
            self.floating_ips_client = FLOAT_CLIENTS[interface](*client_args)
            self.snapshots_client = SNAPSHOTS_CLIENTS[interface](*client_args)
            self.volumes_client = VOLUMES_CLIENTS[interface](*client_args)
            self.volume_types_client = \
                VOLUME_TYPES_CLIENTS[interface](*client_args)
            self.identity_client = IDENTITY_CLIENT[interface](*client_args)
            self.token_client = TOKEN_CLIENT[interface](self.config)
            self.security_groups_client = \
                SECURITY_GROUPS_CLIENT[interface](*client_args)
            self.interfaces_client = INTERFACES_CLIENT[interface](*client_args)
            self.fixed_ips_client = FIXED_IPS_CLIENT[interface](*client_args)
            self.services_client = SERVICES_CLIENT[interface](*client_args)
            self.tenant_usages_client = \
                TENANT_USAGES_CLIENT[interface](*client_args)
            self.hypervisor_client = HYPERVISOR_CLIENT[interface](*client_args)

            if client_args_v3_auth:
                self.servers_client_v3_auth = SERVERS_CLIENTS[interface](
                    *client_args_v3_auth)
            else:
                self.servers_client_v3_auth = None

        except KeyError:
            msg = "Unsupported interface type `%s'" % interface
            raise exceptions.InvalidConfiguration(msg)
        self.network_client = NetworkClient(*client_args)
        self.hosts_client = HostsClientJSON(*client_args)


class AltManager(Manager):

    """
    Manager object that uses the alt_XXX credentials for its
    managed client objects
    """

    def __init__(self):
        conf = config.FuelConfig()
        super(AltManager, self).__init__(conf.identity.alt_username,
                                         conf.identity.alt_password,
                                         conf.identity.alt_tenant_name)


class AdminManager(Manager):

    """
    Manager object that uses the admin credentials for its
    managed client objects
    """

    def __init__(self, interface='json'):
        conf = config.FuelConfig()
        super(AdminManager, self).__init__(conf.identity.admin_username,
                                           conf.identity.admin_password,
                                           conf.identity.admin_tenant_name,
                                           interface=interface)


class ComputeAdminManager(Manager):

    """
    Manager object that uses the compute_admin credentials for its
    managed client objects
    """

    def __init__(self, interface='json'):
        conf = config.FuelConfig()
        base = super(ComputeAdminManager, self)
        base.__init__(conf.compute_admin.username,
                      conf.compute_admin.password,
                      conf.compute_admin.tenant_name,
                      interface=interface)
