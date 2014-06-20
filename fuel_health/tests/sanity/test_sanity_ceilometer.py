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

from fuel_health import ceilometermanager


class CeilometerApiTests(ceilometermanager.CeilometerBaseTest):
    """
    TestClass contains tests that check basic Ceilometer functionality.
    """

    def test_list_meters(self):
        """List ceilometer availability
        Target component: Ceilometer

        Scenario:
            1. Request the list of meters
            2. Request the list of alarms
            3. Request the list of resources.

        Duration: 180 s.
        Deployment tags: Ceilometer
        """
        fail_msg = "Meter list unavailable"

        self.verify(60, self.ceilometer_client.meters.list,
                    1, fail_msg, "Meter listing")

        fail_msg = "Alarm list unavailable"

        self.verify(60, self.ceilometer_client.alarms.list,
                    2, fail_msg, "Alarm listing")

        fail_msg = 'Resource list is unavailable. '

        self.verify(60, self.ceilometer_client.resources.list,
                    3, fail_msg, "Resource listing")
