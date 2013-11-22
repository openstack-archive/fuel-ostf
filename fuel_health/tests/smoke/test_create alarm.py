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
from fuel_health import ceilometermanager

LOG = logging.getLogger(__name__)


class CeilometerApiTests(ceilometermanager.CeilometerBaseTest):
    """
    TestClass contains tests that check basic Compute functionality.
    """

    def test_create_alarm(self):
        """Creates alarm
        Test checks that the creation alarm is available.
        Target component: Ceilometer

        Scenario:
            1. Create a new alarm.
            2. Update the alarm.
            3. Get alarm history.
            4. Change alarm state to 'ok'.
            5. Verify state.
            6. Delete the alarm.

        Duration: 10 s.
        """
        fail_msg = "Creation alarm failed."

        list_meters_resp = self.verify(20, self.list_meters,
                                       1, fail_msg, "meter listing")
        project_id = list_meters_resp[0].project_id
        user_id = list_meters_resp[0].user_id

        create_alarm_resp = self.verify(20, self.create_alarm,
                                        1, fail_msg, "alarm_create",
                                        project_id=project_id,
                                        user_id=user_id,
                                        meter_name=self.name,
                                        threshold='1',
                                        name=self.name)

        fail_msg = "Alarm update failed."

        alarm_update_resp = self.verify(20, self.alarm_update,
                                        1, fail_msg, "alarm_update",
                                        alarm_id=self.get_alarm_id(),
                                        threshold='50')

        fail_msg = "Get alarm history failed."

        alarm_history_resp = self.verify(20, self.alarm_history,
                                         1, fail_msg, "alarm_history",
                                         alarm_id=self.get_alarm_id())

        fail_msg = "Alarm setting state failed."

        alarm_state_resp = self.verify(20, self.set_state,
                                       1, fail_msg, "set_state",
                                       alarm_id=self.get_alarm_id(),
                                       state=self.state_ok)

        fail_msg = "Alarm verify state failed."

        alarm_state_resp = self.verify(20, self.verify_state,
                                       1, fail_msg, "verify_state",
                                       alarm_id=self.get_alarm_id(),
                                       state=self.state_ok)

        fail_msg = "Alarm delete."
        alarm_history_resp = self.verify(20, self.delete_alarm,
                                         1, fail_msg, "delete_alarm",
                                         alarm_id=self.get_alarm_id())


