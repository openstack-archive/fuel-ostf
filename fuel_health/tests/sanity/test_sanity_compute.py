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

import logging

from fuel_health import nmanager

LOG = logging.getLogger(__name__)


class SanityComputeTest(nmanager.SanityChecksTest):
    """TestClass contains tests that check basic Compute functionality."""

    def test_list_instances(self):
        """Request instance list
        Target component: Nova

        Scenario:
            1. Request the list of instances.
        Duration: 20 s.
        """
        fail_msg = 'Instance list is unavailable. '
        self.verify(20, self._list_instances,
                    1, fail_msg, "instance listing",
                    self.compute_client)

    def test_list_images(self):
        """Request image list using Nova
        Target component: Nova

        Scenario:
            1. Request the list of images.
        Duration: 20 s.
        """
        fail_msg = 'Images list is unavailable. '
        self.verify(20, self._list_images,
                    1, fail_msg, "images listing",
                    self.compute_client)

    def test_list_volumes(self):
        """Request volume list
        Target component: Cinder

        Scenario:
            1. Request the list of volumes.
        Duration: 20 s.
        """
        fail_msg = 'Volume list is unavailable. '
        self.verify(20, self._list_volumes,
                    1, fail_msg, "volume listing",
                    self.volume_client)

    def test_list_snapshots(self):
        """Request snapshot list
        Target component: Cinder

        Scenario:
            1. Request the list of snapshots.
        Duration: 20 s.
        """
        fail_msg = 'Snapshots list is unavailable. '
        self.verify(20, self._list_snapshots,
                    1, fail_msg, "snapshots listing",
                    self.volume_client)

    def test_list_flavors(self):
        """Request flavor list
        Target component: Nova

        Scenario:
            1. Request the list of flavors.
            2. Confirm that a response is received.
        Duration: 20 s.
        """
        fail_msg = 'Flavors list is unavailable. '
        list_flavors_resp = self.verify(30, self._list_flavors,
                                        1, fail_msg, "flavor listing",
                                        self.compute_client)

        self.verify_response_true(list_flavors_resp,
                                  "Step 2 failed: {msg}".format(msg=fail_msg))

    def test_list_rate_limits(self):
        """Request absolute limits list
        Target component: Nova

        Scenario:
            1. Request the list of limits.
            2. Confirm that a response is received.
        Duration: 20 s.
        """
        fail_msg = 'Limits list is unavailable. '

        list_limits_resp = self.verify(20, self._list_limits,
                                       1, fail_msg, "limits listing",
                                       self.compute_client)

        self.verify_response_true(
            list_limits_resp, "Step 2 failed: {msg}".format(msg=fail_msg))
