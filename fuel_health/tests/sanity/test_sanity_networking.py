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
        """Networks availability
        Test checks that available networks can be listed.
        Target component: Nova Networking.

        Scenario:
            1. Request list of networks.
            2. Check response.
        Duration: 1-20 s.
        """
        fail_msg = "Network list is unavailable. "
        networks = self.verify(20, self._list_networks, 1,
                               fail_msg,
                               "networks listing",
                               self.compute_client)

        self.verify_response_true(len(networks) >= 0,
                                  'Step 2 failed:'.join(fail_msg))

