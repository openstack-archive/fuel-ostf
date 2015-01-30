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


class FlavorsAdminTest(nmanager.SmokeChecksTest):
    """Tests for flavor creation that require admin privileges."""

    def test_create_flavor(self):
        """Create instance flavor
        Target component: Nova

        Scenario:
            1. Create small-size flavor.
            2. Check that created flavor has the expected name.
            3. Check that the flavor disk has the expected size.
            4. Delete created flavor.
        Duration: 30 s.
        """
        fail_msg = "Flavor was not created properly."
        flavor = self.verify(30, self._create_flavors, 1,
                             fail_msg,
                             "flavor creation",
                             self.compute_client, 255, 1)

        msg_s2 = "Flavor name is not the same as requested."
        self.verify_response_true(
            flavor.name.startswith('ost1_test-flavor'),
            'Step 2 failed: {msg}'.format(msg=msg_s2))

        msg_s3 = "Disk size is not the same as requested."
        self.verify_response_body_value(
            body_structure=flavor.disk,
            value=1, msg=msg_s3, failed_step=3)

        msg_s4 = "Flavor failed to be deleted."
        self.verify(30, self._delete_flavors, 4, msg_s4,
                    "flavor deletion", self.compute_client, flavor)
