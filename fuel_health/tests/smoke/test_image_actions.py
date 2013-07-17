import logging
from nose.plugins.attrib import attr
from nose.tools import timed


from fuel_health.common.utils.data_utils import rand_name
from fuel_health import nmanager


LOG = logging.getLogger(__name__)


class TestImageAction(nmanager.OfficialClientTest):
    """
    Test class verifies the following:
      - verify image can be created;
      - verify that instance can be booted from created image
      - verify snapshot can be created from instance;
      - verify instance can be booted from snapshot.
    """

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
        self.verify_response_body_content(
            name, server.name,
            msg="Looks like Glance service doesn`t work properly.")
        self._wait_for_server_status(server, 'ACTIVE')
        server = client.servers.get(server)  # getting network information
        LOG.debug("server:%s" % server)
        return server

    def _add_keypair(self):
        name = rand_name('ost1_test-keypair-')
        self.keypair = self.compute_client.keypairs.create(name=name)
        self.addCleanup(self.compute_client.keypairs.delete, self.keypair)
        self.verify_response_body_content(
            name, self.keypair.name,
            msg="Looks like Nova service doesn`t work properly.")

    def _create_image(self, server):
        snapshot_name = rand_name('ost1_test-snapshot-')
        create_image_client = self.compute_client.servers.create_image
        image_id = create_image_client(server, snapshot_name)
        self.addCleanup(self.image_client.images.delete, image_id)
        self._wait_for_server_status(server, 'ACTIVE')
        self._wait_for_image_status(image_id, 'active')
        snapshot_image = self.image_client.images.get(image_id)
        self.verify_response_body_content(
            snapshot_name, snapshot_image.name,
            msg="Looks like Glance service doesn`t work properly.")
        return image_id

    @attr(type=['sanity', 'fuel'])
    @timed(130.9)
    def test_snapshot(self):
        """Test instance can be booted and snapshoted from new image.
        Target component: Glance

        Scenario:
            1. Create new keypair to boot an instance.
            2. Check response status equals 200.
            3. Boot default image.
            4. Check response status equals 200.
            5. Check server attributes and status.
            6. Make snapshot of created server.
            7. Boot another instance from created snapshot.
        Duration: 80-131 s.
        """
        # prepare for booting an instance
        self._add_keypair()
        #self._create_security_group_rule()

        # boot a instance and create a timestamp file in it
        server = self._boot_image(nmanager.get_image_from_name())

        # snapshot the instance
        snapshot_image_id = self._create_image(server)

        # boot a second instance from the snapshot
        self._boot_image(snapshot_image_id)
