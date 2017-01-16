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

from oslo_log import log as logging

from fuel_health.common.utils.data_utils import rand_name
from fuel_health import nmanager

LOG = logging.getLogger(__name__)


class TestInstanceLiveMigration(nmanager.NovaNetworkScenarioTest):
    """Test suit verifies:
     - Instance creation
     - Floating ip creation
     - Migrate instance
    """
    @classmethod
    def setUpClass(cls):
        super(TestInstanceLiveMigration, cls).setUpClass()
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
        super(TestInstanceLiveMigration, self).setUp()
        self.check_clients_state()
        if not self.config.compute.compute_nodes and \
           self.config.compute.libvirt_type != 'vcenter':
            self.skipTest('There are no compute nodes')
        if len(self.config.compute.compute_nodes) < 2:
            self.skipTest('To test live migration at least'
                          ' 2 compute nodes are needed')

    def tearDown(self):
        super(TestInstanceLiveMigration, self).tearDown()
        if self.manager.clients_initialized:
            if self.servers:
                for server in self.servers:
                    try:
                        self._delete_server(server)
                        self.servers.remove(server)
                    except Exception:
                        LOG.exception("Server {0} already \
                                      deleted.".format(server))

    def test_001_live_migration(self):
        """Instance live migration
        Target component: Nova

        Scenario:
            1. Create a new security group.
            2. Create an instance using the new security group.
            3. Assign floating ip
            4. Check instance connectivity by floating ip
            5. Find host to migrate
            6. Migrate instance
            7. Check instance host
            8. Check connectivity to migrated instance by floating ip
            9. Remove floating ip
            10. Delete instance.
        Duration: 200 s.
        Deployment tags: ephemeral_ceph
        Available since release: 2014.2-6.1
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

        name = rand_name('ost1_test-server-smoke-migrate-')
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

        self.verify(20, self._assign_floating_ip_to_instance,
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
                    30, (9, 60))

        free_host = self.verify(
            20,
            self.get_free_host,
            5,
            "Can not find free host for instance migration.",
            'free host for migration', server)

        LOG.debug('Free host for migration is {0}'.format(free_host))

        migrate_server = self.verify(
            300,
            self.migrate_instance,
            6,
            "Instance migration failed", 'Instance migration',
            server, free_host)

        LOG.debug('Migrated instance {0}'.format(migrate_server))

        self.verify_response_body_content(
            free_host, self.get_instance_host(migrate_server),
            msg='Server failed to migrate',
            failed_step='7')

        self.verify(600, self._check_vm_connectivity, 8,
                    "VM connectivity doesn`t function properly.",
                    'VM connectivity checking', ip_address,
                    30, (9, 60))

        self.verify(20, self.compute_client.servers.remove_floating_ip,
                    9, "Floating IP cannot be removed.",
                    "removing floating IP", migrate_server, floating_ip)

        self.verify(20, self.compute_client.floating_ips.delete,
                    9, "Floating IP cannot be deleted.",
                    "floating IP deletion", floating_ip)

        if self.floating_ips:
            self.floating_ips.remove(floating_ip)

        self.verify(30, self._delete_server, 10,
                    "Server can not be deleted.",
                    "server deletion", server)
