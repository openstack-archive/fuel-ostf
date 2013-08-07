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


class SanityComputeTest(nmanager.SanityChecksTest):
    """
    TestClass contains tests that check basic Compute functionality.
    """

    @attr(type=['sanity', 'fuel'])
    def test_list_instances(self):
        """Instance list availability
        Test checks that the list of instances is available.
        Target component: Nova
        Scenario:
            1. Request the list of instances.
            2. Confirm that a response is received.
        Duration: 1-20 s.
        """
        fail_msg = 'Instance list is unavailable. '
        list_instance_resp = self.verify(20, self._list_instances,
                                         1, fail_msg, "instance listing",
                                         self.compute_client)

        self.verify_response_true(
            len(list_instance_resp) >= 0, "Step 2 failed: {msg}".format(msg=fail_msg))

    @attr(type=['sanity', 'fuel'])
    def test_list_images(self):
        """Images list availability
        Test checks that the list of images is available.
        Target component: Glance
        Scenario:
            1. Request the list of images.
            2. Confirm that a response is received.
        Duration: 1-20 s.
        """
        fail_msg = 'Images list is unavailable. '
        list_images_resp = self.verify(20, self._list_images,
                                       1, fail_msg, "images listing",
                                       self.compute_client)

        self.verify_response_true(
            len(list_images_resp) >= 0, "Step 2 failed: {msg}".format(msg=fail_msg))

    @attr(type=['sanity', 'fuel'])
    def test_list_volumes(self):
        """Volume list availability
        Test checks that the list of volumes is available.
        Target component: Cinder

        Scenario:
            1. Request the list of volumes.
            2. Confirm that a response is received.
        Duration: 1-20 s.
        """
        fail_msg = 'Volume list is unavailable. '
        list_volumes_resp = self.verify(20, self._list_volumes,
                                        1, fail_msg, "volume listing",
                                        self.volume_client)

        self.verify_response_true(
            len(list_volumes_resp) >= 0, "Step 2 failed: {msg}".format(msg=fail_msg))

    @attr(type=['sanity', 'fuel'])
    def test_list_snapshots(self):
        """Snapshots list availability
        Test checks that the list of snapshots is available.
        Target component: Glance

        Scenario:
            1. Request the list of snapshots.
            2. Confirm that a response is received.
        Duration: 1-20 s.
        """
        fail_msg = 'Snapshots list is unavailable. '
        list_snapshots_resp = self.verify(20, self._list_snapshots,
                                          1, fail_msg, "snapshots listing",
                                          self.volume_client)
        self.verify_response_true(
            len(list_snapshots_resp) >= 0, "Step 2 failed: {msg}".format(msg=fail_msg))

    @attr(type=['sanity', 'fuel'])
    def test_list_flavors(self):
        """Flavor list availability
        Test checks that the list of flavors is available.
        Target component: Nova

        Scenario:
            1. Request the list of flavors.
            2. Confirm that a response is received.
        Duration: 1-20 s.
        """
        fail_msg = 'Flavors list is unavailable. '
        list_flavors_resp = self.verify(30, self._list_flavors,
                                        1, fail_msg, "flavor listing",
                                        self.compute_client)

        self.verify_response_true(
            len(list_flavors_resp) >= 0, "Step 2 failed: {msg}".format(msg=fail_msg))

    @attr(type=['sanity', 'fuel'])
    def test_list_rate_limits(self):
        """Limits list availability
        Test checks that the list of absolute limits is available.
        Target component: Nova

        Scenario:
            1. Request the list of limits.
            2. Confirm that a response is received.
        Duration: 2-20 s.
        """
        fail_msg = 'Limits list is unavailable. '

        list_limits_resp = self.verify(20, self._list_limits,
                                       1, fail_msg, "limits listing",
                                       self.compute_client)

        self.verify_response_true(
            list_limits_resp, "Step 2 failed: {msg}".format(msg=fail_msg))
