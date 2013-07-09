import logging
import subprocess

# Default client libs
import cinderclient.client
import glanceclient
import keystoneclient.v2_0.client
import novaclient.client
try:

    from quantumclient.common import exceptions as exc
    import quantumclient.v2_0.client

except ImportError:
    pass

from fuel_health.common import network_common as net_common
from fuel_health.common import ssh
from fuel_health.common.utils.data_utils import rand_name
from fuel_health import exceptions
import fuel_health.manager
import fuel_health.test


LOG = logging.getLogger(__name__)


class OfficialClientManager(fuel_health.manager.Manager):
    """
    Manager that provides access to the official python clients for
    calling various OpenStack APIs.
    """

    NOVACLIENT_VERSION = '2'
    CINDERCLIENT_VERSION = '1'

    def __init__(self):
        super(OfficialClientManager, self).__init__()
        self.compute_client = self._get_compute_client()
        self.image_client = self._get_image_client()
        self.identity_client = self._get_identity_client()
        self.network_client = self._get_network_client()
        self.volume_client = self._get_volume_client()
        self.client_attr_names = [
            'compute_client',
            'image_client',
            'identity_client',
            'network_client',
            'volume_client'
        ]

    def _get_compute_client(self, username=None, password=None,
                            tenant_name=None):
        # Novaclient will not execute operations for anyone but the
        # identified user, so a new client needs to be created for
        # each user that operations need to be performed for.
        if not username:
            username = self.config.identity.username
        if not password:
            password = self.config.identity.password
        if not tenant_name:
            tenant_name = self.config.identity.tenant_name

        if None in (username, password, tenant_name):
            msg = ("Missing required credentials for compute client. "
                   "username: %(username)s, password: %(password)s, "
                   "tenant_name: %(tenant_name)s") % locals()
            raise exceptions.InvalidConfiguration(msg)

        auth_url = self.config.identity.uri
        dscv = self.config.identity.disable_ssl_certificate_validation

        client_args = (username, password, tenant_name, auth_url)

        # Create our default Nova client to use in testing
        service_type = self.config.compute.catalog_type
        return novaclient.client.Client(self.NOVACLIENT_VERSION,
                                        *client_args,
                                        service_type=service_type,
                                        no_cache=True,
                                        insecure=dscv)

    def _get_image_client(self):
        keystone = self._get_identity_client()
        token = keystone.auth_token
        endpoint = keystone.service_catalog.url_for(service_type='image',
                                                    endpoint_type='publicURL')
        dscv = self.config.identity.disable_ssl_certificate_validation
        return glanceclient.Client('1', endpoint=endpoint, token=token,
                                   insecure=dscv)

    def _get_volume_client(self, username=None, password=None,
                           tenant_name=None):
        if not username:
            username = self.config.identity.username
        if not password:
            password = self.config.identity.password
        if not tenant_name:
            tenant_name = self.config.identity.tenant_name

        auth_url = self.config.identity.uri
        return cinderclient.client.Client(self.CINDERCLIENT_VERSION,
                                          username,
                                          password,
                                          tenant_name,
                                          auth_url)

    def _get_identity_client(self, username=None, password=None,
                             tenant_name=None):
        # This identity client is not intended to check the security
        # of the identity service, so use admin credentials by default.
        if not username:
            username = self.config.identity.admin_username
        if not password:
            password = self.config.identity.admin_password
        if not tenant_name:
            tenant_name = self.config.identity.admin_tenant_name

        if None in (username, password, tenant_name):
            msg = ("Missing required credentials for identity client. "
                   "username: %(username)s, password: %(password)s, "
                   "tenant_name: %(tenant_name)s") % locals()
            raise exceptions.InvalidConfiguration(msg)

        auth_url = self.config.identity.uri
        dscv = self.config.identity.disable_ssl_certificate_validation

        return keystoneclient.v2_0.client.Client(username=username,
                                                 password=password,
                                                 tenant_name=tenant_name,
                                                 auth_url=auth_url,
                                                 insecure=dscv)

    def _get_network_client(self):
        # The intended configuration is for the network client to have
        # admin privileges and indicate for whom resources are being
        # created via a 'tenant_id' parameter.  This will often be
        # preferable to authenticating as a specific user because
        # working with certain resources (public routers and networks)
        # often requires admin privileges anyway.
        username = self.config.identity.admin_username
        password = self.config.identity.admin_password
        tenant_name = self.config.identity.admin_tenant_name

        if None in (username, password, tenant_name):
            msg = ("Missing required credentials for network client. "
                   "username: %(username)s, password: %(password)s, "
                   "tenant_name: %(tenant_name)s") % locals()
            raise exceptions.InvalidConfiguration(msg)

        auth_url = self.config.identity.uri
        dscv = self.config.identity.disable_ssl_certificate_validation

        return quantumclient.v2_0.client.Client(username=username,
                                                password=password,
                                                tenant_name=tenant_name,
                                                auth_url=auth_url,
                                                insecure=dscv)


class OfficialClientTest(fuel_health.test.TestCase):

    manager_class = OfficialClientManager

    @classmethod
    def tearDownClass(cls):
        while cls.os_resources:
            thing = cls.os_resources.pop()
            LOG.debug("Deleting %r from shared resources of %s" %
                      (thing, cls.__name__))

            try:
                # OpenStack resources are assumed to have a delete()
                # method which destroys the resource...
                thing.delete()
            except Exception as e:
                # If the resource is already missing, mission accomplished.
                if e.__class__.__name__ == 'NotFound':
                    continue
                raise

            def is_deletion_complete():
                # Deletion testing is only required for objects whose
                # existence cannot be checked via retrieval.
                if isinstance(thing, dict):
                    return True
                try:
                    thing.get()
                except Exception as e:
                    # Clients are expected to return an exception
                    # called 'NotFound' if retrieval fails.
                    if e.__class__.__name__ == 'NotFound':
                        return True
                    raise
                return False

            # Block until resource deletion has completed or timed-out
            fuel_health.test.call_until_true(is_deletion_complete, 10, 1)


class NovaNetworkScenarioTest(OfficialClientTest):
    """
    Base class for nova network scenario tests
    """

    @classmethod
    def check_preconditions(cls):
        if cls.config.network.quantum_available:
            cls.enabled = False
            msg = "Nova Networking not available"
            raise cls.skipException(msg)
        else:
            cls.enabled = True
            # ensure the config says true
            try:
                cls.compute_client.networks.list()
            except exc.EndpointNotFound:
                cls.enabled = False
                raise


    @classmethod
    def setUpClass(cls):
        super(NovaNetworkScenarioTest, cls).setUpClass()
        cls.tenant_id = cls.manager._get_identity_client(
            cls.config.identity.username,
            cls.config.identity.password,
            cls.config.identity.tenant_name).tenant_id
        cls.network = []
        cls.floating_ips = []

    def _create_keypair(self, client, namestart='ost1_test-keypair-smoke-'):
        kp_name = rand_name(namestart)
        keypair = client.keypairs.create(kp_name)
        self.verify_response_body_content(keypair.id,
                                          kp_name,
                                          'Creation of keypair failed')
        self.set_resource(kp_name, keypair)
        return keypair

    def _create_security_group(self, client, namestart='ost1_test-secgroup-smoke-'):
        # Create security group
        sg_name = rand_name(namestart)
        sg_desc = sg_name + " description"
        secgroup = client.security_groups.create(sg_name, sg_desc)
        self.verify_response_body_content(secgroup.name,
                                          sg_name,
                                          "Security group creation failed")
        self.verify_response_body_content(secgroup.description,
                                          sg_desc,
                                          "Security group creation failed")
        self.set_resource(sg_name, secgroup)

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
                client.security_group_rules.create(secgroup.id, **ruleset)
            except Exception:
                self.fail("Failed to create rule in security group.")

        return secgroup

    def _create_network(self, label='ost1_test-network-smoke-'):
        n_label = rand_name(label)
        cidr = self.config.network.tenant_network_cidr
        networks = self.compute_client.networks.create(label=n_label, cidr=cidr)
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
                cls.compute_client.networks.delete(net)
        except Exception:
            pass

    def _list_networks(self):
        nets = self.compute_client.networks.list()
        return nets

    def _create_server(self, client, name, key_name, security_groups):
        flavor_id = self.config.compute.flavor_ref
        base_image_id = self.config.compute.image_ref
        create_kwargs = {

            'key_name': key_name,
            'security_groups': security_groups,
        }
        server = client.servers.create(name, base_image_id, flavor_id,
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

    def _create_floating_ip(self):
        floating_ips_pool = self.compute_client.floating_ip_pools.list()

        if len(floating_ips_pool):
            floating_ip = self.compute_client.floating_ips.create(
                pool=floating_ips_pool[0].name)

            self.floating_ips.append(floating_ip)
            return floating_ip
        else:
            self.fail('Incorrect OpenStack configurations. '
                      'There is no any floating_ips pools')

    def _assign_floating_ip_to_instance(self, client, server, floating_ip):
        try:
            client.servers.add_floating_ip(server, floating_ip)
        except Exception:
            self.fail('Can not assign floating ip to instance')

    @classmethod
    def _clean_floating_is(cls):
        for ip in cls.floating_ips:
            cls.compute_client.floating_ips.delete(ip)

    def _ping_ip_address(self, ip_address):
        cmd = ['ping', '-c1', '-w1', ip_address]

        def ping():
            proc = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            proc.wait()
            if proc.returncode == 0:
                return True

        # TODO Allow configuration of execution and sleep duration.
        return fuel_health.test.call_until_true(ping, 40, 1)

    def _is_reachable_via_ssh(self, ip_address, username, private_key,
                              timeout=120):
        ssh_client = ssh.Client(ip_address, username,
                                pkey=private_key,
                                timeout=timeout)
        return ssh_client.test_connection_auth()

    def _check_vm_connectivity(self, ip_address, username, private_key,
                               timeout=120):
        self.assertTrue(self._ping_ip_address(ip_address),
                        "Timed out waiting for %s to become "
                        "reachable. Please, check Network "
                        "configuration" % ip_address)

    @classmethod
    def tearDownClass(cls):
        super(NovaNetworkScenarioTest, cls).tearDownClass()
        cls._clean_floating_is()
        cls._clear_networks()
