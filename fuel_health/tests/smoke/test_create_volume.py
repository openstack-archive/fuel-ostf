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

from fuel_health import nmanager


LOG = logging.getLogger(__name__)


class VolumesTest(nmanager.SmokeChecksTest):

    @classmethod
    def setUpClass(cls):
        super(VolumesTest, cls).setUpClass()

    def setUp(self):
        super(VolumesTest, self).setUp()
        if not (self.config.volume.cinder_node_exist
                and self.config.volume.ceph_exist):
            self.fail('There are no cinder nodes or ceph storage for volume')
        if not self.config.compute.compute_nodes:
            self.fail('There are no compute nodes')

    @classmethod
    def tearDownClass(cls):
        super(VolumesTest, cls).tearDownClass()

    def _wait_for_volume_status(self, volume, status):
        self.status_timeout(self.volume_client.volumes, volume.id, status)

    def _wait_for_instance_status(self, server, status):
        self.status_timeout(self.compute_client.servers, server.id, status)

    @attr(type=["fuel", "smoke"])
    def test_volume_create(self):
        """Create instance volume
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
        Duration: 200 s.
        """

        msg_s1 = 'Volume was not created.'

        #Create volume
        volume = self.verify(120, self._create_volume, 1,
                             msg_s1,
                             "volume creation",
                             self.volume_client)

        self.verify(200, self._wait_for_volume_status, 2,
                    msg_s1,
                    "volume becoming 'available'",
                    volume, 'available')

        self.verify_response_true(
            volume.display_name.startswith('ost1_test-volume'),
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

        self.attached = True

        # get volume details
        volume_details = self.verify(20, self.volume_client.volumes.get, 8,
                                     "Can not retrieve volume "
                                     "details. ",
                                     "retreiving volume details",
                                     volume.id)

        # detach volume
        self.verify(50, self._detach_volume, 9,
                    'Can not detach volume. ',
                    "volume detachment",
                    self.volume_client, volume)

        self.verify(120, self._wait_for_volume_status, 10,
                    'Volume status did not become "available".',
                    "volume becoming 'available'",
                    volume, 'available')

        self.verify(50, self.volume_client.volumes.delete, 11,
                    'Can not delete volume. ',
                    "volume deletion",
                    volume)
