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
    def setUp(self):
        super(CeilometerBaseTest, self).setUp()
        if not self.ceilometer_client:
            self.fail('Ceilometer is unavailable.')
        self.name = rand_name('ost1_test-')
        self.meter_name = 'image'
        self.state_ok = 'ok'
        alarm_id = self.get_alarm_id()

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

    def create_sample(self, resource_id,
                            counter_name,
                            counter_type,
                            counter_unit,
                            counter_volume,
                            resource_metadata):
        """
        This method provide creation of sample
        """
        return self.ceilometer_client.samples.create(
                                    resource_id=resource_id,
                                    counter_name=counter_name,
                                    counter_type=counter_type,
                                    counter_unit=counter_unit,
                                    counter_volume=counter_volume,
                                    resource_metadata=resource_metadata)

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
