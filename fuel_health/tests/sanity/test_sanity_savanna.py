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


class SanitySavannaTests(nmanager.SanityChecksTest):
    """
    TestClass contains tests that check basic Savanna functionality.
    """

    @attr(type=['sanity', 'fuel'])
    def test_list_cluster_templates(self):
        """Test checks cluster template creation with
        configuration | JT + NN | TT + DN |.
        Test checks that the list of instances is available.
        Target component: Savanna
        Scenario:
            1. Request the list of cluster templates.
        Duration: 20 s.
        """
        fail_msg = 'Cluster templates is unavailable'
        list_cluster_templates_resp = self.verify(20,
                                                  self._list_cluster_templates,
                                                  1, fail_msg,
                                                  "cluster template listing",
                                                  self.savanna_client)


