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


class SanityIdentityTest(nmanager.SanityChecksTest):
    """
    TestClass contains tests that check basic authentication functionality.
    Special requirements: OS admin user permissions are needed
    """

    @attr(type=['sanity', 'fuel'])
    def test_list_services(self):
        """Services list availability
        Test checks that active services can be listed.
        Target component: Nova

        Scenario:
            1. Request the list of services.
            2. Confirm that a response is received.
        Duration: 20 s.
        """
        fail_msg = 'Services list is unavailable. '
        services = self.verify(20, self._list_services,
                               1, fail_msg, "services listing",
                               self.compute_client)

        self.verify_response_true(services,
                                  "Step 2 failed: {msg}".format(msg=fail_msg))

    @attr(type=['sanity', 'fuel'])
    def test_list_users(self):
        """User list availability
        Test checks that existing users can be listed.
        Target component: Keystone

        Scenario:
            1. Request the list of users.
            2. Confirm that a response is received.
        Duration: 20 s.
        """
        fail_msg = 'User list is unavailable. '
        users = self.verify(20, self._list_users,
                            1, fail_msg, "user listing",
                            self.identity_client)

        self.verify_response_true(users,
                                  "Step 2 failed: {msg}".format(msg=fail_msg))
