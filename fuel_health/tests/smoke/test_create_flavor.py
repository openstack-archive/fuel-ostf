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

""" Test module contains tests for flavor creation/deletion. """


class FlavorsAdminTest(nmanager.SmokeChecksTest):
    """Tests for flavor creation that require admin privileges."""

    _interface = 'json'

    @attr(type=["fuel", "smoke"])
    def test_create_flavor(self):
        """Create instance flavor
        Test check that low requirements flavor can be created
        Target component: Nova

        Scenario:
            1. Create small-size flavor.
            2. Check created flavor has expected name.
            3. Check flavor disk has expected size.
        Duration: 1-30 s.
        """
        fail_msg = "Flavor was not created properly."
        flavor = self.verify(30, self._create_flavors, 1,
                             fail_msg,
                             "flavor creation",
                             self.compute_client, 255, 1)

        msg_s2 = "Flavor name is not the same as requested."
        self.verify_response_true(
            flavor.name.startswith('ost1_test-flavor'),
            'Step 2 failed: '.join(msg_s2))

        msg_s3 = "Disk size is not the same as requested."
        self.verify_response_body_value(
            flavor.disk, 1,
            "Step 3 failed: ".join(msg_s3))
