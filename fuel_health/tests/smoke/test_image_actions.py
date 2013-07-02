import logging

from fuel_health.common.utils.data_utils import rand_name
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
        self.verify_response_body_content(name, server.name)
        self._wait_for_server_status(server, 'ACTIVE')
        server = client.servers.get(server)  # getting network information
        LOG.debug("server:%s" % server)
        return server

    def _add_keypair(self):
        name = rand_name('ost1_test-keypair-')
        self.keypair = self.compute_client.keypairs.create(name=name)
        self.addCleanup(self.compute_client.keypairs.delete, self.keypair)
        self.verify_response_body_content(name, self.keypair.name)

    def _create_image(self, server):
        snapshot_name = rand_name('ost1_test-snapshot-')
        create_image_client = self.compute_client.servers.create_image
        image_id = create_image_client(server, snapshot_name)
        self.addCleanup(self.image_client.images.delete, image_id)
        self._wait_for_server_status(server, 'ACTIVE')
        self._wait_for_image_status(image_id, 'active')
        snapshot_image = self.image_client.images.get(image_id)
        self.verify_response_body_content(snapshot_name, snapshot_image.name)
        return image_id

    def test_snapshot(self):
        # prepare for booting a instance
        self._add_keypair()
        #self._create_security_group_rule()

        # boot a instance and create a timestamp file in it
        server = self._boot_image(self.config.compute.image_ref)

        # snapshot the instance
        snapshot_image_id = self._create_image(server)

        # boot a second instance from the snapshot
        self._boot_image(snapshot_image_id)
