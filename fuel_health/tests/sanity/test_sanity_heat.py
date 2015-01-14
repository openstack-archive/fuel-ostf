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


class SanityHeatTest(nmanager.SanityChecksTest):
    """Class contains tests that check basic Heat functionality.
    Special requirements:
        1. Heat component should be installed.
    """

    def test_list_stacks(self):
        """Request stack list
        Target component: Heat

        Scenario:
            1. Request the list of stacks.

        Duration: 20 s.
        """
        self.verify(20, self._list_stacks, 1,
                    'Stack list is unavailable. ',
                    "stack listing",
                    self.heat_client)
