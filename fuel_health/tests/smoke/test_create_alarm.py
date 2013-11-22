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


class CeilometerApiSmokeTests(ceilometermanager.CeilometerBaseTest):
    """
    TestClass contains tests that check basic Ceilometer functionality.
    """

    def test_create_alarm(self):
        """Ceilometer create, update, check, delete alarm.
        Target component: Ceilometer

        Scenario:
            1. Create a new alarm.
            2. Update the alarm.
            3. Get alarm history.
            4. Change alarm state to 'ok'.
            5. Verify state.
            6. Delete the alarm.

        Deployment tags: Ceilometer
        Duration: 40 s.
        """
        fail_msg = "Creation alarm failed."

        list_meters_resp = self.verify(5, self.list_meters,
                                       1, fail_msg, "meter listing")
        project_id = list_meters_resp[0].project_id
        user_id = list_meters_resp[0].user_id

        create_alarm_resp = self.verify(5, self.create_alarm,
                                        1, fail_msg, "Alarm_create",
                                        project_id=project_id,
                                        user_id=user_id,
                                        meter_name=self.meter_name,
                                        threshold='1',
                                        name=self.name)

        fail_msg = "Alarm update failed."

        alarm_update_resp = self.verify(5, self.alarm_update,
                                        2, fail_msg, "Alarm_update",
                                        alarm_id=self.get_alarm_id(),
                                        threshold='50')

        fail_msg = "Get alarm history failed."

        alarm_history_resp = self.verify(5, self.alarm_history,
                                         3, fail_msg, "Alarm_history",
                                         alarm_id=self.get_alarm_id())

        fail_msg = "Alarm setting state failed."

        alarm_state_resp = self.verify(5, self.set_state,
                                       4, fail_msg, "Set_state",
                                       alarm_id=self.get_alarm_id(),
                                       state=self.state_ok)

        fail_msg = "Alarm verify state failed."

        alarm_state_resp = self.verify(5, self.verify_state,
                                       5, fail_msg, "Verify_state",
                                       alarm_id=self.get_alarm_id(),
                                       state=self.state_ok)

        fail_msg = "Alarm delete."
        alarm_history_resp = self.verify(5, self.delete_alarm,
                                         6, fail_msg, "Delete_alarm",
                                         alarm_id=self.get_alarm_id())
