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


class NetworksTest(nmanager.SanityChecksTest):
    """
    TestClass contains tests check base networking functionality
    """

    @attr(type=['sanity', 'fuel'])
    def test_list_networks(self):
        """Request list of networks
        Target component: Nova Networking.

        Scenario:
            1. Request the list of networks.
            2. Confirm that a response is received.
        Duration: 20 s.
        """
        fail_msg = "Networks list is unavailable. "
        networks = self.verify(20, self._list_networks, 1,
                               fail_msg,
                               "listing networks",
                               self.compute_client)

        self.verify_response_true(networks,
                                  "Step 2 failed: {msg}".format(msg=fail_msg))
