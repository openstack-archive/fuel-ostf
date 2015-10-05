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

from datetime import datetime as dt
from datetime import timedelta as td

from fuel_health import ceilometermanager
from fuel_health.common.utils.data_utils import rand_name


class CeilometerApiSmokeTests(ceilometermanager.CeilometerBaseTest):
    """
    TestClass contains tests that check basic Ceilometer functionality.
    """

    def test_create_alarm(self):
        """Ceilometer create, update, check, delete alarm
        Target component: Ceilometer

        Scenario:
            1. Wait for statistic of metric.
            2. Create a new alarm.
            3. List alarms
            4. Wait for 'ok' alarm state.
            5. Update the alarm.
            6. Wait for 'alarm' alarm state.
            7. Get alarm history.
            8. Change alarm state to 'ok'.
            9. Verify state.
            10. Delete the alarm.
        Duration: 1500 s.
        Deployment tags: Ceilometer
        """

        # TODO(vrovachev): refactor this test suite after resolve bug:
        # https://bugs.launchpad.net/fuel/+bug/1314196

        fail_msg = "Getting statistic of metric is failed."
        msg = "Getting statistic of metric is successful."
        hour_ago = (dt.utcnow() - td(hours=1)).isoformat()
        query = [{'field': 'timestamp', 'op': 'gt', 'value': hour_ago}]

        self.verify(600, self.wait_for_statistic_of_metric, 1,
                    fail_msg, msg,
                    meter_name='image', query=query)

        fail_msg = "Creation of alarm is failed."
        msg = "Creation of alarm is successful."

        alarm = self.verify(60, self.create_alarm, 2,
                            fail_msg, msg,
                            meter_name='image',
                            threshold=0.9,
                            name=rand_name('ceilometer-alarm'),
                            period=600,
                            statistic='avg',
                            comparison_operator='lt')

        fail_msg = 'Getting alarms is failed.'
        msg = 'Getting alarms is successful.'
        query = [{'field': 'project', 'op': 'eq', 'value': alarm.project_id}]

        self.verify(60, self.ceilometer_client.alarms.list, 3,
                    fail_msg, msg, q=query)

        fail_msg = "Alarm status is not equal 'ok'."
        msg = "Alarm status is 'ok'."

        self.verify(1000, self.wait_for_alarm_status, 4,
                    fail_msg, msg,
                    alarm.alarm_id, 'ok')

        fail_msg = "Alarm update failed."
        msg = "Alarm was updated."

        self.verify(60, self.ceilometer_client.alarms.update, 5,
                    fail_msg, msg,
                    alarm_id=alarm.alarm_id,
                    threshold=1.1)

        fail_msg = "Alarm verify state is failed."
        msg = "Alarm status is 'alarm'."

        self.verify(1000, self.wait_for_alarm_status, 6,
                    fail_msg, msg,
                    alarm.alarm_id, 'alarm')

        fail_msg = "Getting history of alarm is failed."
        msg = 'Getting alarms history is successful.'

        self.verify(60, self.ceilometer_client.alarms.get_history, 7,
                    fail_msg, msg,
                    alarm_id=alarm.alarm_id)

        fail_msg = "Setting alarm state to 'insufficient data' is failed."
        msg = "Set alarm state to 'insufficient data'."

        self.verify(60, self.ceilometer_client.alarms.set_state, 8,
                    fail_msg, msg,
                    alarm_id=alarm.alarm_id,
                    state='insufficient data')

        fail_msg = "Alarm state verification is failed."
        msg = "Alarm state verification is successful."

        self.verify(60, self.verify_state, 9,
                    fail_msg, msg,
                    alarm_id=alarm.alarm_id,
                    state='insufficient data')

        fail_msg = "Alarm deleting is failed."
        msg = "Alarm deleted."

        self.verify(60, self.ceilometer_client.alarms.delete, 10,
                    fail_msg, msg,
                    alarm_id=alarm.alarm_id)
