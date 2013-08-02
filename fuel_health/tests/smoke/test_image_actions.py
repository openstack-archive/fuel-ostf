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
from nose.plugins.attrib import attr


from fuel_health.common.utils.data_utils import rand_name
from fuel_health import nmanager


LOG = logging.getLogger(__name__)


class TestImageAction(nmanager.SmokeChecksTest):
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
        self.status_timeout(self.compute_client.images, image_id, status)

    def _boot_image(self, image_id):
        name = rand_name('ost1_test-image')
        client = self.compute_client
        flavor_id = self._create_nano_flavor()
        LOG.debug("name:%s, image:%s" % (name, image_id))
        server = client.servers.create(name=name,
                                       image=image_id,
                                       flavor=flavor_id)
        self.set_resource(name, server)
        #self.addCleanup(self.compute_client.servers.delete, server)
        self.verify_response_body_content(
            name, server.name,
            msg="Please, refer to OpenStack logs for more details.")
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
            msg="Please, refer to OpenStack logs for more details.")
        return image_id

    @attr(type=['sanity', 'fuel'])
    def test_snapshot(self):
        """Launch instance, create snapshot, launch instance from snapshot
        Target component: Glance

        Scenario:
            1. Boot default image.
            2. Make snapshot of created server.
            3. Delete instance created in step 1.
            4. Boot another instance from created snapshot.
        Duration: 80-180 s.
        """
        server = self.verify(180, self._boot_image, 2,
                             "Image can not be booted.",
                             "image booting",
                             nmanager.get_image_from_name())

        # snapshot the instance
        snapshot_image_id = self.verify(180, self._create_image, 3,
                                        "Snapshot of an"
                                        " instance can not be made.",
                                        'snapshotting an instance',
                                        server)
        
        self.verify(180, self.compute_client.servers.delete, 4,
                    "Instance can not be deleted.",
                    'Instance deletion',
                    server)
            
        self.verify(180, self._boot_image, 5,
                    "Instance can not be booted from snapshot.",
                    'booting instance from snapshot',
                    snapshot_image_id)
