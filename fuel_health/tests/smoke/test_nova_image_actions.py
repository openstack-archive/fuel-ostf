# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Mirantis, Inc.
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

import logging
import traceback

from fuel_health.common.utils.data_utils import rand_name
from fuel_health import nmanager
from fuel_health import test


LOG = logging.getLogger(__name__)


class TestImageAction(nmanager.SmokeChecksTest):
    """
    Test class verifies the following:
      - verify that image can be created;
      - verify that instance can be booted from created image;
      - verify that snapshot can be created from an instance;
      - verify that instance can be booted from a snapshot.
    """
    @classmethod
    def setUpClass(cls):
        super(TestImageAction, cls).setUpClass()
        if cls.manager.clients_initialized:
            cls.smoke_flavor = cls._create_nano_flavor()

    @classmethod
    def tearDownClass(cls):
        super(TestImageAction, cls).tearDownClass()

    def setUp(self):
        super(TestImageAction, self).setUp()
        self.check_clients_state()
        if not self.config.compute.compute_nodes and \
           self.config.compute.libvirt_type != 'vcenter':
            self.skipTest('There are no compute nodes')
        self.check_image_exists()

    def _wait_for_server_status(self, server, status):
        self.status_timeout(self.compute_client.servers,
                            server.id,
                            status)

    def _wait_for_image_status(self, image_id, status):
        self.status_timeout(self.compute_client.images, image_id, status)

    def _wait_for_server_deletion(self, server):
        def is_deletion_complete():
                # Deletion testing is only required for objects whose
                # existence cannot be checked via retrieval.
                if isinstance(server, dict):
                    return True
                try:
                    server.get()
                except Exception as e:
                    # Clients are expected to return an exception
                    # called 'NotFound' if retrieval fails.
                    if e.__class__.__name__ == 'NotFound':
                        return True
                    self.error_msg.append(e)
                    LOG.debug(traceback.format_exc())
                return False

        # Block until resource deletion has completed or timed-out
        test.call_until_true(is_deletion_complete, 10, 1)

    def _boot_image(self, image_id):
        name = rand_name('ost1_test-image')
        client = self.compute_client
        flavor_id = self.smoke_flavor
        LOG.debug("name:%s, image:%s" % (name, image_id))
        if 'neutron' in self.config.network.network_provider:
            network = [net.id for net in
                       self.compute_client.networks.list()
                       if net.label == self.private_net]
            if network:
                create_kwargs = {
                    'nics': [
                        {'net-id': network[0]},
                    ],
                }
            else:
                self.fail("Default private network '{}' isn't present."
                          "Please verify it is properly created.".
                          format(self.private_net))
            server = client.servers.create(name=name,
                                           image=image_id,
                                           flavor=flavor_id, **create_kwargs)
        else:
            server = client.servers.create(name=name,
                                           image=image_id,
                                           flavor=flavor_id)
        self.set_resource(name, server)
        # self.addCleanup(self.compute_client.servers.delete, server)
        self.verify_response_body_content(
            name, server.name,
            msg="Please refer to OpenStack logs for more details.")
        self._wait_for_server_status(server, 'ACTIVE')
        server = client.servers.get(server)  # getting network information
        LOG.debug("server:%s" % server)
        return server

    def _create_image(self, server):
        snapshot_name = rand_name('ost1_test-snapshot-')
        create_image_client = self.compute_client.servers.create_image
        image_id = create_image_client(server, snapshot_name)
        self.addCleanup(self.compute_client.images.delete, image_id)
        self._wait_for_server_status(server, 'ACTIVE')
        self._wait_for_image_status(image_id, 'ACTIVE')
        snapshot_image = self.compute_client.images.get(image_id)
        self.verify_response_body_content(
            snapshot_name, snapshot_image.name,
            msg="Please refer to OpenStack logs for more details.")
        return image_id

    def test_snapshot(self):
        """Launch instance, create snapshot, launch instance from snapshot
        Target component: Glance

        Scenario:
            1. Get existing image by name.
            2. Launch an instance using the default image.
            3. Make snapshot of the created instance.
            4. Delete the instance created in step 1.
            5. Wait while instance deleted
            6. Launch another instance from the snapshot created in step 2.
            7. Delete server.
        Duration: 300 s.
        """
        image = self.verify(30, self.get_image_from_name, 1,
                            "Image can not be retrieved.",
                            "getting image by name")

        server = self.verify(180, self._boot_image, 2,
                             "Image can not be booted.",
                             "image booting",
                             image)

        # snapshot the instance
        snapshot_image_id = self.verify(180, self._create_image, 3,
                                        "Snapshot of an"
                                        " instance can not be created.",
                                        'snapshotting an instance',
                                        server)

        self.verify(180, self.compute_client.servers.delete, 4,
                    "Instance can not be deleted.",
                    'Instance deletion',
                    server)

        self.verify(180, self._wait_for_server_deletion, 5,
                    "Instance can not be deleted.",
                    'Wait for instance deletion complete',
                    server)

        server = self.verify(180, self._boot_image, 6,
                             "Instance can not be launched from snapshot.",
                             'booting instance from snapshot',
                             snapshot_image_id)

        self.verify(30, self._delete_server, 7,
                    "Server can not be deleted.",
                    "server deletion", server)
