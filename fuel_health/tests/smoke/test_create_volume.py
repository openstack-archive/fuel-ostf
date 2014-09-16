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

from fuel_health import nmanager


LOG = logging.getLogger(__name__)


class VolumesTest(nmanager.SmokeChecksTest):

    @classmethod
    def setUpClass(cls):
        super(VolumesTest, cls).setUpClass()
        if cls.manager.clients_initialized:
            cls.smoke_flavor = cls._create_nano_flavor()

    def setUp(self):
        super(VolumesTest, self).setUp()
        self.check_clients_state()
        if (not self.config.volume.cinder_node_exist
                and not self.config.volume.ceph_exist):
            self.skipTest('There are no cinder nodes or '
                          'ceph storage for volume')
        if not self.config.compute.compute_nodes \
                and self.config.compute.libvirt_type != 'vcenter':
            self.skipTest('There are no compute nodes')
        self.check_image_exists()

    @classmethod
    def tearDownClass(cls):
        super(VolumesTest, cls).tearDownClass()

    def _wait_for_volume_status(self, volume, status):
        self.status_timeout(self.volume_client.volumes, volume.id, status)

    def _wait_for_instance_status(self, server, status):
        self.status_timeout(self.compute_client.servers, server.id, status)

    def test_volume_create(self):
        """Create volume and attach it to instance
        Target component: Compute

        Scenario:
            1. Create a new small-size volume.
            2. Wait for volume status to become "available".
            3. Check volume has correct name.
            4. Create new instance.
            5. Wait for "Active" status
            6. Attach volume to an instance.
            7. Check volume status is "in use".
            8. Get information on the created volume by its id.
            9. Detach volume from the instance.
            10. Check volume has "available" status.
            11. Delete volume.
            12. Verify that volume deleted
            13. Delete server.
        Duration: 350 s.
        """

        msg_s1 = 'Volume was not created.'

        # Create volume
        volume = self.verify(120, self._create_volume, 1,
                             msg_s1,
                             "volume creation",
                             self.volume_client)

        self.verify(200, self._wait_for_volume_status, 2,
                    msg_s1,
                    "volume becoming 'available'",
                    volume, 'available')

        self.verify_response_true(
            volume.display_name.startswith('ostf-test-volume'),
            'Step 3 failed: {msg}'.format(msg=msg_s1))

        # create instance
        instance = self.verify(200, self._create_server, 4,
                               "Instance creation failed. ",
                               "server creation",
                               self.compute_client)

        self.verify(200, self._wait_for_instance_status, 5,
                    'Instance status did not become "available".',
                    "instance becoming 'available'",
                    instance, 'ACTIVE')

        # Attach volume
        self.verify(120, self._attach_volume_to_instance, 6,
                    'Volume couldn`t be attached.',
                    'volume attachment',
                    volume, instance.id)

        self.verify(180, self._wait_for_volume_status, 7,
                    'Attached volume status did not become "in-use".',
                    "volume becoming 'in-use'",
                    volume, 'in-use')

        # get volume details
        self.verify(20, self.volume_client.volumes.get, 8,
                    "Can not retrieve volume details. ",
                    "retrieving volume details", volume.id)

        # detach volume
        self.verify(50, self._detach_volume, 9,
                    'Can not detach volume. ',
                    "volume detachment",
                    instance.id, volume.id)

        self.verify(120, self._wait_for_volume_status, 10,
                    'Volume status did not become "available".',
                    "volume becoming 'available'",
                    volume, 'available')

        self.verify(50, self.volume_client.volumes.delete, 11,
                    'Can not delete volume. ',
                    "volume deletion",
                    volume)

        self.verify(50, self.verify_volume_deletion, 12,
                    'Can not delete volume. ',
                    "volume deletion",
                    volume)

        self.verify(30, self._delete_server, 13,
                    "Can not delete server. ",
                    "server deletion",
                    instance)

    def test_create_boot_volume(self):
        """Create volume and boot instance from it
        Target component: Compute

        Scenario:
            1. Create a new small-size volume from image.
            2. Wait for volume status to become "available".
            3. Launch instance from created volume.
            4. Wait for "Active" status.
            5. Delete instance.
            6. Delete volume.
            7. Verify that volume deleted
        Duration: 350 s.
        """
        fail_msg_step_1 = 'Volume was not created'
        # Create volume
        volume = self.verify(120, self._create_boot_volume, 1,
                             fail_msg_step_1,
                             "volume creation",
                             self.volume_client)

        self.verify(200, self._wait_for_volume_status, 2,
                    fail_msg_step_1,
                    "volume becoming 'available'",
                    volume, 'available')

        # create instance
        instance = self.verify(200, self.create_instance_from_volume, 3,
                               "Instance creation failed. ",
                               "server creation",
                               self.compute_client, volume)

        self.verify(200, self._wait_for_instance_status, 4,
                    'Instance status did not become "available".',
                    "instance becoming 'available'",
                    instance, 'ACTIVE')

        self.verify(30, self._delete_server, 5,
                    "Can not delete server. ",
                    "server deletion",
                    instance)

        self.verify(50, self.volume_client.volumes.delete, 6,
                    'Can not delete volume. ',
                    "volume deletion",
                    volume)

        self.verify(50, self.verify_volume_deletion, 7,
                    'Can not delete volume. ',
                    "volume deletion",
                    volume)
