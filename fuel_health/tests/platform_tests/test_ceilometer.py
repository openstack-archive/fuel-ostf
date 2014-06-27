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


class CeilometerApiPlatformTests(ceilometermanager.CeilometerBaseTest):
    """
    TestClass contains tests that check basic Ceilometer functionality.
    """

    def test_check_alarm_state(self):
        """Ceilometer test to check alarm status and get Nova notifications.
        Target component: Ceilometer

        Scenario:
            1. Create a new instance.
            2. Instance become active.
            3. Wait for Nova notifications.
            4. Wait for Nova statistic.
            5. Create a new alarm.
            6. Verify that become status 'alarm' or 'ok'.
        Duration: 800 s.

        Deployment tags: Ceilometer
        """

        self.check_image_exists()

        name = rand_name('ost1-test-ceilo-instance-')

        fail_msg = "Creation instance is failed."
        msg = "Instance was created."

        self.instance = self.verify(600, self._create_server, 1,
                                    fail_msg, msg,
                                    self.compute_client, name)

        fail_msg = "Instance is not available."
        msg = "instance becoming available."

        self.verify(200, self.wait_for_instance_status, 2,
                    fail_msg, msg,
                    self.instance, 'ACTIVE')

        fail_msg = "Nova notifications is not received."
        msg = "Nova notifications is received."
        query = [{'field': 'resource', 'op': 'eq', 'value': self.instance.id}]

        self.verify(600, self.wait_notifications, 3,
                    fail_msg, msg, self.nova_notifications, query)

        fail_msg = "Statistic for Nova notification:vcpus is not received."
        msg = "Statistic for Nova notification:vcpus is received."

        vcpus_stat = self.verify(60, self.wait_for_statistic_of_metric, 4,
                                 fail_msg, msg,
                                 self.nova_notifications[1],
                                 query)

        fail_msg = "Creation alarm for sum vcpus is failed."
        msg = "Creation alarm for sum vcpus is successful."
        threshold = vcpus_stat[0].sum - 1

        alarm = self.verify(60, self.create_alarm, 5,
                            fail_msg, msg,
                            meter_name=self.nova_notifications[1],
                            threshold=threshold,
                            name=rand_name('ceilometer-alarm'),
                            period=600,
                            statistic='sum',
                            comparison_operator='lt')

        fail_msg = "Alarm verify state is failed."
        msg = "Alarm status becoming."

        self.verify(1000, self.wait_for_alarm_status, 6,
                    fail_msg, msg,
                    alarm.alarm_id)

    def test_create_sample(self):
        """Ceilometer create, check, list samples
        Target component: Ceilometer

        Scenario:
        1. Getting samples for existing resource (the default image).
        2. Create sample for existing resource (the default image).
        3. Check that created sample has the expected resource.
        4. Getting samples after create sample.
        5. Comparison sample lists before and after create sample.
        Duration: 40 s.
        Deployment tags: Ceilometer
        """

        self.check_image_exists()
        image_id = self.get_image_from_name()
        query = [{'field': 'resource', 'op': 'eq', 'value': image_id}]

        fail_msg = 'Getting samples for update image is failed.'
        msg = 'Getting samples for update image is successful.'

        list_before_create_sample = self.verify(
            60, self.ceilometer_client.samples.list, 1,
            fail_msg, msg,
            self.glance_notifications[0], q=query)

        fail_msg = 'Creation sample for update image is failed.'
        msg = 'Creation sample for update image is successful.'

        sample = self.verify(60, self.ceilometer_client.samples.create, 2,
                             fail_msg, msg,
                             resource_id=image_id,
                             counter_name=self.glance_notifications[0],
                             counter_type='delta',
                             counter_unit='image',
                             counter_volume=1,
                             resource_metadata={"user": "example_metadata"})

        fail_msg = 'Resource of sample is absent or not equal with expected.'

        self.verify_response_body_value(
            body_structure=sample[0].resource_id,
            value=image_id,
            msg=fail_msg,
            failed_step=3)

        fail_msg = 'Getting samples after create sample is failed.'
        msg = 'Getting samples after create sample is successful.'

        list_after_create_sample = self.verify(
            60, self.ceilometer_client.samples.list, 4,
            fail_msg, msg,
            self.glance_notifications[0], q=query)

        fail_msg = 'Samples list after create sample not greater than ' \
                   'samples list before create sample.'
        msg = 'Samples list after create sample greater than samples list' \
              ' before create sample.'

        self.verify(1, self.assertGreater, 5,
                    fail_msg, msg,
                    len(list_after_create_sample),
                    len(list_before_create_sample))

    def test_check_volume_notifications(self):
        """Ceilometer test to check get Cinder notifications.
        Target component: Ceilometer

        Scenario:
        1. Create volume.
        2. Check volume notifications.
        Duration: 100 s.
        Deployment tags: Ceilometer
        """

        if (not self.config.volume.cinder_node_exist
                and not self.config.volume.ceph_exist):
            self.fail('There are no cinder nodes or ceph storage for volume')

        fail_msg = "Creation volume failed"
        msg = "Volume was created"

        volume = self.verify(60, self._create_volume, 1,
                             fail_msg, msg,
                             self.volume_client,
                             'available')

        query = [{'field': 'resource', 'op': 'eq', 'value': volume.id}]
        fail_msg = "Volume notifications is not received"
        msg = "Volume notifications is received"

        self.verify(600, self.wait_notifications, 2,
                    fail_msg, msg,
                    self.volume_notifications, query)

    def test_check_glance_notifications(self):
        """Ceilometer test to check get Glance notifications.
        Target component: Ceilometer

        Scenario:
        1. Check glance notifications.
        Duration: 300 s.
        Deployment tags: Ceilometer
        """
        query = [{'field': 'resource', 'op': 'eq',
                  'value': self.get_image_from_name()}]

        fail_msg = "Glance notifications is not received"
        msg = "Glance notifications is received"

        self.verify(600, self.wait_notifications, 1,
                    fail_msg, msg,
                    self.glance_notifications, query)
