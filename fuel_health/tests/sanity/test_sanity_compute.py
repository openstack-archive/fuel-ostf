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


class SanityComputeTest(nmanager.SanityChecksTest):
    """
    TestClass contains tests check base Compute functionality.
    """
    _interface = 'json'

    @attr(type=['sanity', 'fuel'])
    @timed(6)
    def test_list_instances(self):
        """Instances list availability
        Test checks that list of instances is available.
        Target component: Nova
        Scenario:
            1. Request list of instances.
            2. Check response.
        Duration: 1-6 s.
        """
        fail_msg = ('Servers list is unavailable. '
                    'Looks like something is broken in Nova.')
        try:
            list_instance_resp = self._list_instances(
                self.compute_client)
        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 1 failed: " + fail_msg)

        self.verify_response_true(
            len(list_instance_resp) >= 0, "Step 2 failed: " + fail_msg)

    @attr(type=['sanity', 'fuel'])
    @timed(8)
    def test_list_images(self):
        """Images list availability
        Test checks that list of images is available.
        Target component: Glance
        Scenario:
            1. Request list of images.
            2. Check response.
        Duration: 1-8 s.
        """
        fail_msg = ('Images list is unavailable. '
                    'Looks like something is broken in Nova or Glance.')
        try:
            list_images_resp = self._list_images(
                self.compute_client)
        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 1 failed: " + fail_msg)

        self.verify_response_true(
            len(list_images_resp) >= 0, "Step 2 failed: " + fail_msg)


    @attr(type=['sanity', 'fuel'])
    @timed(6)
    def test_list_volumes(self):
        """Volumes list availability
        Test checks that list of volumes is available.
        Target component: Swift

        Scenario:
            1. Request list of volumes.
            2. Check response.
        Duration: 1-6 s.
        """
        fail_msg = ('Volumes list is unavailable. '
                    'Looks like something is broken in Nova or Cinder.')
        try:
            list_volumes_resp = self._list_volumes(
                self.volume_client)
        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 1 failed: " + fail_msg)

        self.verify_response_true(
            len(list_volumes_resp) >= 0, "Step 2 failed: " + fail_msg)

    @attr(type=['sanity', 'fuel'])
    @timed(6)
    def test_list_snapshots(self):
        """Snapshots list availability
        Test checks that list of snapshots is available.
        Target component: Glance

        Scenario:
            1. Request list of snapshots.
            2. Check response.
        Duration: 1-6 s.
        """
        fail_msg = ('Snapshots list is unavailable. '
                    'Looks like something is broken in Nova or Cinder.')
        try:
            list_snapshots_resp = self._list_snapshots(
                self.volume_client)
        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 1 failed: " + fail_msg)

        self.verify_response_true(
            len(list_snapshots_resp) >= 0, "Step 2 failed: " + fail_msg)


    @attr(type=['sanity', 'fuel'])
    @timed(6)
    def test_list_flavors(self):
        """Flavors list availability
        Test checks that list of flavors is available.
        Target component: Nova

        Scenario:
            1. Request list of flavors.
            2. Check response.
        Duration: 1-6 s.
        """
        fail_msg = ('Flavors list is unavailable. '
                    'Looks like something is broken in Nova.')
        try:
            list_flavors_resp = self._list_flavors(
                self.compute_client)
        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 1 failed: " + fail_msg)

        self.verify_response_true(
            len(list_flavors_resp) >= 0, "Step 2 failed: " + fail_msg)

    @attr(type=['sanity', 'fuel'])
    @timed(6)
    def test_list_rate_limits(self):
        """Limits list availability
        Test checks that list of absolute limits is available.
        Target component: Nova

        Scenario:
            1. Request list of limits.
            2. Check response.
        Duration: 2-6 s.
        """
        fail_msg = ('Limits list is unavailable. '
                    'Looks like something is broken in Nova.')
        try:
            list_limits_resp = self._list_limits(
                self.compute_client)

        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 1 failed: " + fail_msg)

        self.verify_response_true(
            list_limits_resp, "Step 2 failed: " + fail_msg)
