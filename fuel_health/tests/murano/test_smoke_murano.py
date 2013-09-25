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

from fuel_health import murano
from fuel_health import heatmanager


class MuranoSmokeTests(heatmanager.HeatBaseTest):
    """
    TestClass contains tests that check core Murano functionality.
    """

    def test_check_default_key_pair(self):
        """Check Default Key Pair 'murano-lb-key' For Server Farms
        Test checks that user has Key Pair 'murano-lb-key'.
        Please, see more detailed information in Murano Administrator Guide.
        Target component: Murano

        Scenario:
            1. Check that Key Pair 'murano-lb-key' exists.
        Duration: 5 s.
        """

        keyname = 'murano-lb-key'
        fail_msg = "Key Pair %s does not exist. " % keyname

        self.verify(5, self.is_keypair_available, 1, fail_msg,
                    "checking if %s keypair is available" % keyname,
                    keyname)

    def test_check_windows_image_with_murano_tag(self):
        """Check Windows Image With Murano Tag
        Test checks that user has windows image with murano tag.
        Please, see more detailed information in Murano Administrator Guide.
        Target component: Murano

        Scenario:
            1. Check that Windows image with Murano tag imported in Glance.
        Duration: 5 s.
        """

        exp_key = 'murano_image_info'
        exp_value = '{"type":"ws-2012-std","title":"Windows Server 2012"}'

        fail_msg = "Windows image with Murano tag wasn't imported into Glance"

        find_image = lambda k, v: len(
            [i for i in self.compute_client.images.list()
             if k in i.metadata and v == i.metadata[k]]) > 0

        self.verify(5, find_image, 1, fail_msg,
                    "checking if Windows image with Murano tag is available",
                    exp_key, exp_value)
