#!/usr/bin/env python
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

from fuel_health.common.utils.data_utils import rand_name
import fuel_health.nmanager
import fuel_health.test

LOG = logging.getLogger(__name__)


class CeilometerBaseTest(fuel_health.nmanager.OfficialClientTest):

    @classmethod
    def setUpClass(cls):
        super(CeilometerBaseTest, cls).setUpClass()
        cls.flavor = cls._create_mini_flavor()
        cls.wait_interval = cls.config.compute.build_interval
        cls.wait_timeout = cls.config.compute.build_timeout
        cls.private_net = 'net04'

    def setUp(self):
        super(CeilometerBaseTest, self).setUp()
        if not self.ceilometer_client:
            self.fail('Ceilometer is unavailable.')
        if not self.config.compute.compute_nodes:
            self.fail('There are no compute nodes')
        self.name = rand_name('ost1_test-alarm_actions')
        self.meter_name = 'cpu'
        self.meter_name_image = 'image'
        self.state_ok = 'ok'
        self.comparison_operator = 'lt'
        self.statistic = 'avg'
        self.instance = object()
        self.period = '600'
        self.threshold = '20'

    def list_meters(self):
        """
        This method allows to get the list of environments.
        Returns the list of environments.
        """
        return self.ceilometer_client.meters.list()

    def list_alarm(self):
        """
        This method list alarms
        """
        return self.ceilometer_client.alarms.list()

    def list_resources(self):
        """
        This method list resources
        """
        return self.ceilometer_client.resources.list()

    def list_statistics(self, meter_name):
        """
        This method list statistics
        """
        return self.ceilometer_client.statistics.list(meter_name)

    def create_alarm(self, **kwargs):
        """
        This method provide creation of alarm
        """
        return self.ceilometer_client.alarms.create(**kwargs)

    def get_alarm_id(self):
        list_alarms_resp = self.list_alarm()
        for alarm_list in list_alarms_resp:
            if alarm_list.name == self.name:
                return alarm_list.alarm_id

    def alarm_update(self, alarm_id, threshold):
        """
        This method provide alarm update
        """

        return self.ceilometer_client.alarms.update(alarm_id=alarm_id,
                                                    threshold=threshold)

    def alarm_history(self, alarm_id):
        """
        This method provide listing alarm history
        """

        return self.ceilometer_client.alarms.get_history(alarm_id=alarm_id)

    def set_state(self, alarm_id, state):
        """
        This method provide setting state
        """
        return self.ceilometer_client.alarms.set_state(alarm_id=alarm_id,
                                                       state=state)

    def get_state(self, alarm_id):
        """
        This method provide getting state
        """
        return self.ceilometer_client.alarms.get_state(alarm_id=alarm_id)

    def verify_state(self, alarm_id, state):
        """
        This method provide getting state
        """
        alarm_state_resp = self.get_state(alarm_id)
        if alarm_state_resp == state:
            pass
        else:
            self.fail('State was not setted')

    def delete_alarm(self, alarm_id):
        """
        This method provide deleting alarm
        """
        return self.ceilometer_client.alarms.delete(alarm_id=alarm_id)

    def _wait_for_instance_metrics(self, server, status):
        self.status_timeout(self.compute_client.servers, server.id, status)

    def wait_for_alarm_status(self, alarm_id):
        """
        The method is a customization of test.status_timeout().
        """
        def check_status():
            alarm_state_resp = self.get_state(alarm_id)
            if alarm_state_resp == 'alarm':
                return True  # All good.
            LOG.debug("Waiting for state to get alarm status.")

        if not fuel_health.test.call_until_true(check_status, 600, 10):
            self.fail("Timed out waiting to become alarm")

    def wait_for_instance_metrics(self, meter_name):
        """
        The method is a customization of test.status_timeout().
        """
        def check_status():
            stat_state_resp = self.list_statistics(meter_name)
            if len(stat_state_resp) > 0:
                return True  # All good.
            LOG.debug("Waiting for state to get state status.")

        if not fuel_health.test.call_until_true(check_status, 600, 10):

            self.fail("Timed out waiting to become alarm")
        else:
            return self.list_statistics(meter_name)

    @classmethod
    def _create_mini_flavor(cls):
        name = rand_name('ost1_test-ceilometer')
        cls.flavor = cls.compute_client.flavors.create(
            name=name, ram=64, vcpus=1, disk=1)
        return cls.flavor

    @classmethod
    def _clean_alarms(cls):
        list_alarms_resp = cls.ceilometer_client.alarms.list()
        for alarm_list in list_alarms_resp:
            if alarm_list.name.startswith('ost1_test-'):
                alarm_id = alarm_list.alarm_id
                cls.ceilometer_client.alarms.delete(alarm_id)

    @classmethod
    def tearDownClass(cls):
        super(CeilometerBaseTest, cls).tearDownClass()
        cls._clean_alarms()
        try:
            cls.compute_client.flavors.delete(cls.flavor.id)
        except Exception as exc:
            LOG.debug(exc)
