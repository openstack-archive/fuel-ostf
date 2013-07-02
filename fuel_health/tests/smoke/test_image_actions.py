import logging

from fuel_health.common.utils.data_utils import rand_name
from fuel_health.common.ssh import Client
from fuel_health import nmanager


LOG = logging.getLogger(__name__)


class TestImageAction(nmanager.OfficialClientTest):

    def _wait_for_server_status(self, server, status):
        self.status_timeout(self.compute_client.servers,
                            server.id,
                            status)

    def _wait_for_image_status(self, image_id, status):
        self.status_timeout(self.image_client.images, image_id, status)

    def _boot_image(self, image_id):
        name = rand_name('ost1_test-image')
        client = self.compute_client
        flavor_id = self.config.compute.flavor_ref
        LOG.debug("name:%s, image:%s" % (name, image_id))
        server = client.servers.create(name=name,
                                       image=image_id,
                                       flavor=flavor_id,
                                       key_name=self.keypair.name)
        self.addCleanup(self.compute_client.servers.delete, server)
        self.assertEqual(name, server.name)
        self._wait_for_server_status(server, 'ACTIVE')
        server = client.servers.get(server)  # getting network information
        LOG.debug("server:%s" % server)
        return server

    def _add_keypair(self):
        name = rand_name('ost1_test-keypair-')
        self.keypair = self.compute_client.keypairs.create(name=name)
        self.addCleanup(self.compute_client.keypairs.delete, self.keypair)
        self.assertEqual(name, self.keypair.name)

    def _create_security_group_rule(self):
        sgs = self.compute_client.security_groups.list()
        for sg in sgs:
            if sg.name == 'default':
                secgroup = sg

        ruleset = {
            # ssh
            'ip_protocol': 'tcp',
            'from_port': 22,
            'to_port': 22,
            'cidr': '0.0.0.0/0',
            'group_id': None
        }
        sg_rule = self.compute_client.security_group_rules.create(secgroup.id,
                                                                  **ruleset)
        self.addCleanup(self.compute_client.security_group_rules.delete,
                        sg_rule.id)

    def _write_timestamp(self, server):
        username = self.config.compute.image_ssh_user
        host = server.networks[self.config.compute.network_for_ssh][0]
        ssh_client = Client(host, username, pkey=self.keypair.private_key)
        ssh_client.exec_command('date > /tmp/timestamp; sync')
        self.timestamp = ssh_client.exec_command('cat /tmp/timestamp')

    def _create_image(self, server):
        snapshot_name = rand_name('ost1_test-snapshot-')
        create_image_client = self.compute_client.servers.create_image
        image_id = create_image_client(server, snapshot_name)
        self.addCleanup(self.image_client.images.delete, image_id)
        self._wait_for_server_status(server, 'ACTIVE')
        self._wait_for_image_status(image_id, 'active')
        snapshot_image = self.image_client.images.get(image_id)
        self.assertEquals(snapshot_name, snapshot_image.name)
        return image_id

    def _check_timestamp(self, server):
        username = self.config.compute.image_ssh_user
        host = server.networks[self.config.compute.network_for_ssh][0]
        ssh_client = Client(host, username, pkey=self.keypair.private_key)
        got_timestamp = ssh_client.exec_command('cat /tmp/timestamp')
        self.assertEqual(self.timestamp, got_timestamp)

    def test_snapshot_pattern(self):
        # prepare for booting a instance
        self._add_keypair()
        self._create_security_group_rule()

        # boot a instance and create a timestamp file in it
        server = self._boot_image(self.config.compute.image_ref)
        self._write_timestamp(server)

        # snapshot the instance
        snapshot_image_id = self._create_image(server)

        # boot a second instance from the snapshot
        server_from_snapshot = self._boot_image(snapshot_image_id)

        # check the existence of the timestamp file in the second instance
        self._check_timestamp(server_from_snapshot)
