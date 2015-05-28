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
from fuel_health.common.utils.data_utils import rand_name


class CeilometerApiSmokeTests(ceilometermanager.CeilometerBaseTest):
    """TestClass contains tests that check basic Ceilometer functionality."""

    def test_create_alarm(self):
        """Ceilometer test to create, update, check and delete alarm
        Target component: Ceilometer

        Scenario:
            1. Get statistic of metric.
            2. Create an alarm.
            3. Get the alarm.
            4. List alarms.
            5. Wait for 'ok' alarm state.
            6. Update the alarm.
            7. Wait for 'alarm' alarm state.
            8. Get the alarm history.
            9. Set the alarm state to 'insufficient data'.
            10. Verify that the alarm state is 'insufficient data'.
            11. Delete the alarm.

        Duration: 120 s.
        Deployment tags: Ceilometer
        """

        fail_msg = 'Failed to get statistic of metric.'
        msg = 'getting statistic of metric'
        self.verify(600, self.wait_for_statistic_of_metric, 1,
                    fail_msg, msg, meter_name='image')

        fail_msg = 'Failed to create alarm.'
        msg = 'creating alarm'
        alarm = self.verify(60, self.create_alarm, 2,
                            fail_msg, msg,
                            meter_name='image',
                            threshold=0.9,
                            name=rand_name('ceilometer-alarm'),
                            period=600,
                            statistic='avg',
                            comparison_operator='lt')

        fail_msg = 'Failed to get alarm.'
        msg = 'getting alarm'
        self.verify(60, self.ceilometer_client.alarms.get, 3,
                    fail_msg, msg, alarm.alarm_id)

        fail_msg = 'Failed to list alarms.'
        msg = 'listing alarms'
        query = [{'field': 'project', 'op': 'eq', 'value': alarm.project_id}]
        self.verify(60, self.ceilometer_client.alarms.list, 4,
                    fail_msg, msg, q=query)

        fail_msg = 'Failed while waiting for alarm state to become "ok".'
        msg = 'waiting for alarm state to become "ok"'
        self.verify(1000, self.wait_for_alarm_status, 5,
                    fail_msg, msg, alarm.alarm_id, 'ok')

        fail_msg = 'Failed to update alarm.'
        msg = 'updating alarm'
        self.verify(60, self.ceilometer_client.alarms.update, 6,
                    fail_msg, msg, alarm_id=alarm.alarm_id, threshold=1.1)

        fail_msg = 'Failed while waiting for alarm state to become "alarm".'
        msg = 'waiting for alarm state to become "alarm"'
        self.verify(1000, self.wait_for_alarm_status, 7,
                    fail_msg, msg, alarm.alarm_id, 'alarm')

        fail_msg = 'Failed to get alarm history.'
        msg = 'getting alarm history'
        self.verify(60, self.ceilometer_client.alarms.get_history, 8,
                    fail_msg, msg, alarm_id=alarm.alarm_id)

        fail_msg = 'Failed to set alarm state to "insufficient data".'
        msg = 'setting alarm state to "insufficient data"'
        self.verify(60, self.ceilometer_client.alarms.set_state, 9,
                    fail_msg, msg, alarm_id=alarm.alarm_id,
                    state='insufficient data')

        fail_msg = 'Failed while verifying alarm state.'
        msg = 'verifying alarm state'
        self.verify(60, self.verify_state, 10,
                    fail_msg, msg, alarm_id=alarm.alarm_id,
                    state='insufficient data')

        fail_msg = 'Failed to delete alarm.'
        msg = 'deleting alarm'
        self.verify(60, self.ceilometer_client.alarms.delete, 11,
                    fail_msg, msg, alarm_id=alarm.alarm_id)
