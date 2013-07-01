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

from fuel_health.common import log as logging
import fuel_health.config
from fuel_health import exceptions
#  REST Fuzz testing client libs
from fuel_health.services.compute.json import flavors_client
from fuel_health.services.compute.json import floating_ips_client
from fuel_health.services.compute.json import hypervisor_client
from fuel_health.services.compute.json import images_client
from fuel_health.services.compute.json import keypairs_client
from fuel_health.services.compute.json import limits_client
from fuel_health.services.compute.json import quotas_client
from fuel_health.services.compute.json import security_groups_client
from fuel_health.services.compute.json import servers_client
from fuel_health.services.network.json import network_client
from fuel_health.services.volume.json import snapshots_client
from fuel_health.services.volume.json import volumes_client

NetworkClient = network_client.NetworkClient
ImagesClient = images_client.ImagesClientJSON
FlavorsClient = flavors_client.FlavorsClientJSON
ServersClient = servers_client.ServersClientJSON
LimitsClient = limits_client.LimitsClientJSON
FloatingIPsClient = floating_ips_client.FloatingIPsClientJSON
SecurityGroupsClient = security_groups_client.SecurityGroupsClientJSON
KeyPairsClient = keypairs_client.KeyPairsClientJSON
VolumesClient = volumes_client.VolumesClientJSON
SnapshotsClient = snapshots_client.SnapshotsClientJSON
QuotasClient = quotas_client.QuotasClientJSON
HypervisorClient = hypervisor_client.HypervisorClientJSON

LOG = logging.getLogger(__name__)


class Manager(object):

    """
    Base manager class

    Manager objects are responsible for providing a configuration object
    and a client object for a test case to use in performing actions.
    """

    def __init__(self):
        self.config = fuel_health.config.FuelConfig()
        self.client_attr_names = []


class FuzzClientManager(Manager):

    """
    Manager class that indicates the client provided by the manager
    is a fuzz-testing client that test contains. These fuzz-testing
    clients are used to be able to throw random or invalid data at
    an endpoint and check for appropriate error messages returned
    from the endpoint.
    """
    pass


class ComputeFuzzClientManager(FuzzClientManager):

    """
    Manager that uses the REST client that can send
    random or invalid data at the OpenStack Compute API
    """

    def __init__(self, username=None, password=None, tenant_name=None):
        """
        We allow overriding of the credentials used within the various
        client classes managed by the Manager object. Left as None, the
        standard username/password/tenant_name is used.

        :param username: Override of the username
        :param password: Override of the password
        :param tenant_name: Override of the tenant name
        """
        super(ComputeFuzzClientManager, self).__init__()

        # If no creds are provided, we fall back on the defaults
        # in the config file for the Compute API.
        username = username or self.config.identity.username
        password = password or self.config.identity.password
        tenant_name = tenant_name or self.config.identity.tenant_name

        if None in (username, password, tenant_name):
            msg = ("Missing required credentials. "
                   "username: %(username)s, password: %(password)s, "
                   "tenant_name: %(tenant_name)s") % locals()
            raise exceptions.InvalidConfiguration(msg)

        auth_url = self.config.identity.uri

        # Ensure /tokens is in the URL for Keystone...
        if 'tokens' not in auth_url:
            auth_url = auth_url.rstrip('/') + '/tokens'

        if self.config.identity.strategy == 'keystone':
            client_args = (self.config, username, password, auth_url,
                           tenant_name)
        else:
            client_args = (self.config, username, password, auth_url)

        self.servers_client = ServersClient(*client_args)
        self.flavors_client = FlavorsClient(*client_args)
        self.images_client = ImagesClient(*client_args)
        self.limits_client = LimitsClient(*client_args)
        self.keypairs_client = KeyPairsClient(*client_args)
        self.security_groups_client = SecurityGroupsClient(*client_args)
        self.floating_ips_client = FloatingIPsClient(*client_args)
        self.volumes_client = VolumesClient(*client_args)
        self.snapshots_client = SnapshotsClient(*client_args)
        self.quotas_client = QuotasClient(*client_args)
        self.network_client = NetworkClient(*client_args)
        self.hypervisor_client = HypervisorClient(*client_args)


class ComputeFuzzClientAltManager(Manager):

    """
    Manager object that uses the alt_XXX credentials for its
    managed client objects
    """

    def __init__(self):
        conf = fuel_health.config.FuelConfig()
        super(ComputeFuzzClientAltManager, self).__init__(
            conf.identity.alt_username,
            conf.identity.alt_password,
            conf.identity.alt_tenant_name)


class ComputeFuzzClientAdminManager(Manager):

    """
    Manager object that uses the alt_XXX credentials for its
    managed client objects
    """

    def __init__(self):
        conf = fuel_health.config.FuelConfig()
        super(ComputeFuzzClientAdminManager, self).__init__(
            conf.compute_admin.username,
            conf.compute_admin.password,
            conf.compute_admin.tenant_name)
