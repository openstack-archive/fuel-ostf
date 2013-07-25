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
from nose.tools import timed

from fuel_health import nmanager


LOG = logging.getLogger(__name__)


class VolumesTest(nmanager.SmokeChecksTest):

    @classmethod
    def setUpClass(cls):
        super(VolumesTest, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(VolumesTest, cls).tearDownClass()

    def _wait_for_volume_status(self, volume_id, status):
        self.status_timeout(self.volume_client.volumes, volume_id, status)

    def _wait_for_instance_status(self, server, status):
        self.status_timeout(self.compute_client.servers, server.id, status)

    @attr(type=["fuel", "smoke"])
    @timed(61)
    def test_volume_create(self):
        """Volume creation
        Target component: Compute

        Scenario:
            1. Create a new small-size volume.
            2. Wait for "available" volume status.
            3. Check response contains "display_name" section.
            4. Create instance and wait for "Active" status
            5. Attach volume to instance.
            6. Check volume status is "in use".
            7. Get created volume information by its id.
            8. Detach volume from instance.
            9. Check volume has "available" status.
            10. Delete volume.
        Duration: 48-61 s.
        """

        msg_s1 = ('Volume is not created. Looks like '
                  'something is broken in Storage.')

        #Create volume
        try:
            volume = self._create_volume(self.volume_client)
        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 1 failed: " + msg_s1)

        try:
            self._wait_for_volume_status(volume.id, 'available')
        except Exception as exc:
            LOG.debug(exc)
            self.fail('Step 2 failed: ' + msg_s1)

        self.verify_response_true(
            volume.display_name.startswith('ost1_test-volume'),
            'Step 3 failed: ' + msg_s1)

        try:
            # create instance
            instance = self._create_server(self.compute_client)
            self._wait_for_instance_status(instance, 'ACTIVE')
        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 4 failed:" + "Instance creation failed."
                                         "Looks like something is "
                                         "broken in Compute")

        # Attach volume
        try:
            self._attach_volume_to_instance(
                self.volume_client.volumes, instance.id, volume)
        except Exception as exc:
            LOG.debug(exc)
            self.fail('Step 5 failed: ' + "Volume attachment failed,"
                                          "Looks like something is "
                                          "broken in Cinder or Nova")

        try:
            self._wait_for_volume_status(volume.id, 'in-use')
            LOG.info(volume.status)
        except Exception as exc:
            LOG.debug(exc)
            self.fail('Step 6 failed: ' + 'Attached volume can not '
                                          'get expected state')

        self.attached = True

        # get volume details
        try:
            volume_details = self.volume_client.volumes.get(volume.id)
            LOG.info(volume_details)
        except Exception as exc:
            LOG.debug(exc)
            self.fail('Step 7 failed:' + "Can not retrieve volume details,"
                                         "Looks like something is broken in Cinder")


        # detach volume
        try:
            self._detach_volume(self.volume_client, volume)
        except Exception as exc:
            LOG.debug(exc)
            self.fail('Step 8 failed:' + 'Can not detach volume,'
                                         'Looks like something  is broken in Cinder')
        try:
            self._wait_for_volume_status(volume.id, 'available')
        except Exception as exc:
            LOG.debug(exc)
            self.fail('Step 9 failed:' + 'Volume does not get available status,'
                                         'Looks like something is broken in Cinder')
        try:
            self.volume_client.volumes.delete(volume)
        except Exception as exc:
            LOG.debug(exc)
            self.fail('Step 10 failed: ' + 'Can not delete volume,'
                                          'Looks like something is broken in Cinder')
