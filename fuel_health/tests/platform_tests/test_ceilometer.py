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
from fuel_health import nmanager
from fuel_health.common.utils.data_utils import rand_name
import time

LOG = logging.getLogger(__name__)


class TestAlarmAction(ceilometermanager.CeilometerBaseTest):
    """
    TestClass contains tests that checks functionality of alarm in Ceilometer.
    Special requirements:
        1. Ceilometer should be installed.
    """

    def setUp(self):
        super(TestAlarmAction, self).setUp()
        self.instance = object()

    def tearDown(self):
        super(TestAlarmAction, self).tearDown()
        self.compute_client.servers.delete(self.instance)

    def _wait_for_instance_status(self, server, status):
        self.status_timeout(self.compute_client.servers, server.id, status)

    def test_alarm_action(self):
        """Check alarm actions
        Test checks that the creation alarm is available.
        And updating status is correctly.
        Target component: Ceilometer

        Scenario:
            1. Create a new instance
            2. Wait for "Active" status
            3. Create a new alarm on exsisting metric (instances's cpu).
            4. Wait the next polling period and state of alarm to 'alarm'.
            5. Delete the alarm.

        Duration: 1200 s.
        """

        fail_msg = "Creation instance failed"

        create_flavor_resp = self._create_nano_flavor()
        flavor = create_flavor_resp.id
        image = nmanager.get_image_from_name()
        name = rand_name('ost1_test-instance-alarm_actions')

        self.instance = self.verify(200, self.compute_client.servers.create, 1,
                               fail_msg,
                               "server creation",
                               name=name,
                               flavor=flavor,
                               image=image)

        self.verify(200, self._wait_for_instance_status, 2,
                    "instance is not available",
                    "instance becoming 'available'",
                    self.instance, 'ACTIVE')

        fail_msg = "Creation alarm failed."

        meter_name = 'cpu'
        period = '600'
        comparison_operator = 'lt'
        statistic = 'avg'
        name = rand_name('ost1_test-alarm_actions')

        statistic_meter_resp = self.list_statistics(meter_name)
        threshold = statistic_meter_resp[0].avg - 1

        create_alarm_resp = self.verify(20, self.create_alarm,
                                        3, fail_msg, "alarm_create",
                                        meter_name=meter_name,
                                        threshold=threshold,
                                        name=name,
                                        period=period,
                                        statistic=statistic,
                                        comparison_operator=comparison_operator
                                        )

        fail_msg = "Alarm verify state failed."

        alarm_state_resp = ''
        while 'alarm' not in alarm_state_resp:
            alarm_state_resp = self.verify(20, self.get_state,
                                           4, fail_msg, "get_state",
                                           alarm_id=create_alarm_resp.alarm_id)
            if 'alarm' not in alarm_state_resp:
                time.sleep(30)
            else:
                break

        fail_msg = "Alarm isn't deleted."
        alarm_delete_resp = self.verify(20, self.delete_alarm,
                                        5, fail_msg, "delete_alarm",
                                        alarm_id=create_alarm_resp.alarm_id)
