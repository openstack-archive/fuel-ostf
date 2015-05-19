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

import datetime

from fuel_health import ceilometermanager


class CeilometerApiTests(ceilometermanager.CeilometerBaseTest):
    """TestClass contains tests that check basic Ceilometer functionality."""

    def test_list_meters(self):
        """Ceilometer test to list meters, alarms, resources and events
        Target component: Ceilometer

        Scenario:
            1. Request the list of meters with query: disk_format=qcow2.
            2. Request the list of alarms.
            3. Request the list of resources created for the last hour.
            4. Request the list of events created for the last hour.

        Duration: 180 s.
        Deployment tags: Ceilometer
        """

        fail_msg = "Failed to get list of meters."
        q = [{"field": "metadata.disk_format", "op": "eq", "value": "qcow2"}]
        self.verify(60, self.ceilometer_client.meters.list,
                    1, fail_msg, "getting list of meters", q)

        fail_msg = "Failed to get list of alarms."
        self.verify(60, self.ceilometer_client.alarms.list,
                    2, fail_msg, "getting list of alarms")

        fail_msg = 'Failed to get list of resources.'
        an_hour_ago = (datetime.datetime.now() -
                       datetime.timedelta(hours=1)).isoformat()
        q = [{"field": "timestamp", "op": "gt", "value": an_hour_ago}]
        self.verify(60, self.ceilometer_client.resources.list,
                    3, fail_msg, "getting list of resources", q)

        fail_msg = 'Failed to get list of events.'
        self.verify(60, self.ceilometer_client.events.list,
                    4, fail_msg, 'getting list of events', q)
