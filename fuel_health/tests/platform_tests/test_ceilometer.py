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
        Duration: 60 s.

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
        1. Request samples list for image resource.
        2. Create new sample for image resource.
        3. Check that created sample has the expected resource.
        4. Get samples and compare sample lists before and after create sample.
        5. Get resource of sample
        Duration: 5 s.
        Deployment tags: Ceilometer
        """

        self.check_image_exists()
        image_id = self.get_image_from_name()
        query = [{'field': 'resource', 'op': 'eq', 'value': image_id}]

        fail_msg = 'Get samples for update image is failed.'
        msg = 'Get samples for update image is successful.'

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

        fail_msg = """List of samples after creating test sample isn't
        greater than initial list of samples"""
        msg = 'New test sample was added to the list of samples'

        self.verify(
            20, self.wait_samples_count, 4,
            fail_msg, msg,
            self.glance_notifications[0], query,
            len(list_before_create_sample))

        fail_msg = 'Getting resource of sample is failed.'
        msg = 'Getting resource of sample is successful.'

        self.verify(self.ceilometer_client.resources.get, 5,
                    fail_msg, msg, sample.resource_id)

    def test_check_volume_notifications(self):
        """Ceilometer test to check get Cinder notifications.
        Target component: Ceilometer

        Scenario:
        1. Create volume.
        2. Check volume notifications.
        Duration: 10 s.
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
        fail_msg = "Volume notifications are not received."
        msg = "Volume notifications are received."

        self.verify(600, self.wait_notifications, 2,
                    fail_msg, msg,
                    self.volume_notifications, query)

    def test_check_glance_notifications(self):
        """Ceilometer test to check get Glance notifications.
        Target component: Ceilometer

        Scenario:
        1. Check glance notifications.
        Duration: 5 s.
        Deployment tags: Ceilometer
        """
        query = [{'field': 'resource', 'op': 'eq',
                  'value': self.get_image_from_name()}]

        fail_msg = "Glance notifications are not received."
        msg = "Glance notifications are received."

        self.verify(600, self.wait_notifications, 1,
                    fail_msg, msg,
                    self.glance_notifications, query)

    def test_check_keystone_notifications(self):
        """Ceilometer test to check get Keystone notifications.
        Target component: Ceilometer

        Scenario:
        1. Check keystone project notifications.
        2. Check keystone user notifications.
        3. Check keystone role notifications.
        4. Check keystone group notifications.
        Duration: 5 s.
        Deployment tags: Ceilometer, 2014.2-6.0
        """

        tenant, user, role, group, trust = self.identity_helper()

        fail_msg = "Keystone project notifications are not received."
        msg = "Keystone project notifications are received."
        query = [{'field': 'resource', 'op': 'eq', 'value': tenant.id}]
        self.verify(600, self.wait_notifications, 1,
                    fail_msg, msg,
                    self.keystone_project_notifications, query)

        fail_msg = "Keystone user notifications are not received."
        msg = "Keystone user notifications are received."
        query = [{'field': 'resource', 'op': 'eq', 'value': user.id}]
        self.verify(600, self.wait_notifications, 2,
                    fail_msg, msg,
                    self.keystone_user_notifications, query)

        fail_msg = "Keystone role notifications are not received."
        msg = "Keystone role notifications are received."
        query = [{'field': 'resource', 'op': 'eq', 'value': role.id}]
        self.verify(600, self.wait_notifications, 3,
                    fail_msg, msg,
                    self.keystone_role_notifications, query)

        fail_msg = "Keystone group notifications are not received."
        msg = "Keystone group notifications are received."
        query = [{'field': 'resource', 'op': 'eq', 'value': group.id}]
        self.verify(600, self.wait_notifications, 4,
                    fail_msg, msg,
                    self.keystone_group_notifications, query)

        fail_msg = "Keystone trust notifications are not received."
        msg = "Keystone trust notifications are received."
        query = [{'field': 'resource', 'op': 'eq', 'value': trust.id}]
        self.verify(600, self.wait_notifications, 5,
                    fail_msg, msg,
                    self.keystone_trust_notifications, query)

    def test_check_neutron_notifications(self):
        """Ceilometer test to check get Neutron notifications.
        Target component: Ceilometer

        Scenario:
        1. Check neutron network notifications.
        2. Check neutron subnet notifications.
        3. Check neutron port notifications.
        4. Check neutron router notifications.
        5. Check neutron floating ip notifications.
        Duration: 40 s.
        Deployment tags: Ceilometer, neutron
        """

        net, subnet, port, router, flip = self.neutron_helper()

        fail_msg = "Neutron network notifications are not received."
        msg = "Neutron network notifications are received."
        query = [{'field': 'resource', 'op': 'eq', 'value': net["id"]}]
        self.verify(60, self.wait_notifications, 1,
                    fail_msg, msg,
                    self.neutron_network_notifications, query)

        fail_msg = "Neutron subnet notifications are not received."
        msg = "Neutron subnet notifications are received."
        query = [{'field': 'resource', 'op': 'eq', 'value': subnet["id"]}]
        self.verify(60, self.wait_notifications, 2,
                    fail_msg, msg,
                    self.neutron_subnet_notifications, query)

        fail_msg = "Neutron port notifications are not received."
        msg = "Neutron port notifications are received."
        query = [{'field': 'resource', 'op': 'eq', 'value': port["id"]}]
        self.verify(60, self.wait_notifications, 3,
                    fail_msg, msg,
                    self.neutron_port_notifications, query)

        fail_msg = "Neutron router notifications are not received."
        msg = "Neutron router notifications are received."
        query = [{'field': 'resource', 'op': 'eq', 'value': router["id"]}]
        self.verify(60, self.wait_notifications, 4,
                    fail_msg, msg,
                    self.neutron_router_notifications, query)

        fail_msg = "Neutron floating ip notifications are not received."
        msg = "Neutron floating ip notifications are received."
        query = [{'field': 'resource', 'op': 'eq', 'value': flip["id"]}]
        self.verify(60, self.wait_notifications, 5,
                    fail_msg, msg,
                    self.neutron_floatingip_notifications, query)

    def test_check_sahara_notifications(self):
        """Ceilometer test to check get Sahara notifications.
        Target component: Ceilometer

        Scenario:
        1. Check Sahara cluster notifications.
        Duration: 5 s.
        Deployment tags: Ceilometer, Sahara
        """

        cluster = self.sahara_helper()

        fail_msg = "Sahara cluster notifications are not received."
        msg = "Sahara cluster notifications are received."
        query = [{'field': 'resource', 'op': 'eq', 'value': cluster.id}]
        self.verify(60, self.wait_notifications, 1,
                    fail_msg, msg,
                    self.sahara_cluster_notifications, query)
