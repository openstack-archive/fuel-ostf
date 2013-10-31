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
        if self.ceilometer_client is None:
            self.fail('Ceilometer is unavailable.')

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

    def create_sample(self, resource_id):
        """
            This method provide creation of sample
        """
        counter_name = rand_name('ost1_test-sample')
        counter_type = 'gauge'
        counter_init = 'B'
        counter_volume = 1
        resource_metadata = {"user" : "example_metadata"}
        return self.ceilometer_client.samples.create(resource_id=resource_id,
                                                     counter_name=counter_name,
                                                     counter_type=counter_type,
                                                     counter_init=counter_init,
                                                     counter_volume=counter_volume,
                                                     resource_metadata=resource_metadata)

