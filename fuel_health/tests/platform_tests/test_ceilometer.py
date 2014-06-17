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

LOG = logging.getLogger(__name__)


class CeilometerApiPlatformTests(ceilometermanager.CeilometerBaseTest):
    """
    TestClass contains tests that check basic Ceilometer functionality.
    """

    def test_check_alarm_state(self):
        """Ceilometer test to check the alarm can change status
        Target component: Ceilometer

        Scenario:
            1. Create a new instance.
            2. Instance become active.
            3. Create metrics for instance.
            4. Create a new alarm.
            5. Verify that status become "alarm".
        Duration: 800 s.

        Deployment tags: Ceilometer
        """

        self.check_image_exists()
        fail_msg = "Creation instance failed"

        create_kwargs = {}
        if 'neutron' in self.config.network.network_provider:
            network = [net.id for net in
                       self.compute_client.networks.list()
                       if net.label == self.private_net]

            create_kwargs = {'nics': [{'net-id': network[0]}]}

        image = self.get_image_from_name()
        name = rand_name('ost1_test-instance-alarm_actions')
        self.instance = self.verify(600, self.compute_client.servers.create, 1,
                                    fail_msg,
                                    "server creation",
                                    name=name,
                                    flavor=self.flavor,
                                    image=image,
                                    **create_kwargs)
        self.set_resource(self.instance.id, self.instance)

        self.verify(200, self._wait_for_instance_metrics, 2,
                    "instance is not available",
                    "instance becoming 'available'",
                    self.instance, 'ACTIVE')

        fail_msg = "Creation metrics failed."

        statistic_meter_resp = self.verify(
            600, self.wait_for_instance_metrics, 3,
            fail_msg, "metrics created", self.meter_name
        )

        fail_msg = "Creation alarm failed."

        threshold = statistic_meter_resp[0].avg - 1
        create_alarm_resp = self.verify(
            5, self.create_alarm,
            4, fail_msg, "alarm_create",
            meter_name=self.meter_name,
            threshold=threshold,
            name=self.name,
            period=self.period,
            statistic=self.statistic,
            comparison_operator=self.comparison_operator
        )

        fail_msg = "Alarm verify state failed."

        self.verify(1000, self.wait_for_alarm_status, 5,
                    fail_msg,
                    "alarm status becoming 'alarm'",
                    create_alarm_resp.alarm_id)

    def test_create_sample(self):
        """Ceilometer create, check sample,check statistics
        Target component: Ceilometer

        Scenario:
        1. Create sample for existing resource (the default image).
        2. Check that created sample has the expected resource.
        3. Check that the sample has the statistic.
        Duration: 40 s.
        Deployment tags: Ceilometer
        """
        self.check_image_exists()
        fail_msg_1 = 'Sample can not be created'

        sample = self.verify(30, self.create_sample, 1,
                             fail_msg_1,
                             "Sample creating",
                             resource_id=self.get_image_from_name(),
                             counter_name=self.meter_name_image,
                             counter_type=self.counter_type,
                             counter_unit=self.counter_unit,
                             counter_volume=self.counter_volume,
                             resource_metadata=self.resource_metadata)

        fail_msg_2 = 'Sample resource is absent'

        self.verify_response_body_value(
            body_structure=sample[0].resource_id,
            value=self.get_image_from_name(),
            msg=fail_msg_2,
            failed_step=2)

        fail_msg_3 = 'Sample statistic list is unavailable.'

        self.verify(5, self.list_statistics, 3,
                    fail_msg_3,
                    "sample statistic",
                    sample[0].counter_name)
