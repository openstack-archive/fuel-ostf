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
import traceback

from fuel_health.common.utils.data_utils import rand_name
import fuel_health.nmanager
import fuel_health.test

LOG = logging.getLogger(__name__)


class CeilometerBaseTest(fuel_health.nmanager.NovaNetworkScenarioTest):
    @classmethod
    def setUpClass(cls):
        super(CeilometerBaseTest, cls).setUpClass()
        if cls.manager.clients_initialized:
            cls.wait_interval = cls.config.compute.build_interval
            cls.wait_timeout = cls.config.compute.build_timeout
            cls.private_net = 'net04'
            cls.alarm_id_list = []
            cls.nova_notifications = ['memory', 'vcpus', 'disk.root.size',
                                      'disk.ephemeral.size']
            cls.neutron_network_notifications = ['network', 'network.create',
                                                 'network.update']
            cls.neutron_subnet_notifications = ['subnet', 'subnet.create',
                                                'subnet.update']
            cls.neutron_port_notifications = ['port', 'port.create',
                                              'port.update']
            cls.neutron_router_notifications = ['router', 'router.create',
                                                'router.update']
            cls.neutron_floatingip_notifications = ['ip.floating.create',
                                                    'ip.floating.update']
            cls.glance_notifications = ['image.update', 'image.upload',
                                        'image.delete', 'image.download',
                                        'image.serve']
            cls.volume_notifications = ['volume', 'volume.size']
            cls.glance_notifications = ['image', 'image.size', 'image.update',
                                        'image.upload', 'image.delete']
            cls.swift_notifications = ['storage.objects.incoming.bytes',
                                       'storage.objects.outgoing.bytes',
                                       'storage.api.request']
            cls.heat_notifications = ['stack.create', 'stack.update',
                                      'stack.delete', 'stack.resume',
                                      'stack.suspend']

    def setUp(self):
        super(CeilometerBaseTest, self).setUp()
        self.check_clients_state()
        if not self.ceilometer_client:
            self.fail('Ceilometer is unavailable.')
        if not self.config.compute.compute_nodes:
            self.fail('There are no compute nodes')

    def create_alarm(self, **kwargs):
        """
        This method provides creation of alarm
        """
        if 'name' in kwargs:
            kwargs['name'] = rand_name(kwargs['name'])
        alarm = self.ceilometer_client.alarms.create(**kwargs)
        if alarm:
            self.alarm_id_list.append(alarm.alarm_id)
            return alarm

    def get_state(self, alarm_id):
        """
        This method provides getting state
        """
        return self.ceilometer_client.alarms.get_state(alarm_id=alarm_id)

    def verify_state(self, alarm_id, state):
        """
        This method provides getting state
        """
        alarm_state_resp = self.get_state(alarm_id)
        if alarm_state_resp == state:
            pass
        else:
            self.fail('State was not setted')

    def wait_for_instance_status(self, server, status):
        self.status_timeout(self.compute_client.servers, server.id, status)

    def wait_for_alarm_status(self, alarm_id, status=None):
        """
        The method is a customization of test.status_timeout().
        """

        def check_status():
            alarm_state_resp = self.get_state(alarm_id)
            if status:
                if alarm_state_resp == status:
                    return True
            elif alarm_state_resp == 'alarm' or 'ok':
                return True  # All good.
            LOG.debug("Waiting for state to get alarm status.")

        if not fuel_health.test.call_until_true(check_status, 1000, 10):
            self.fail("Timed out waiting to become alarm")

    def wait_for_sample_of_metric(self, metric, query=None, limit=100):
        """
        This method is to wait for sample to add it to database.
        query example:
        query=[
        {'field':'resource',
        'op':'eq',
        'value':'000e6838-471b-4a14-8da6-655fcff23df1'
        }]
        """

        def check_status():
            body = self.ceilometer_client.samples.list(meter_name=metric,
                                                       q=query, limit=limit)
            if body:
                return True

        if fuel_health.test.call_until_true(check_status, 600, 10):
            return self.ceilometer_client.samples.list(meter_name=metric,
                                                       q=query, limit=limit)
        else:
            self.fail("Timed out waiting to become sample for metric:{metric}"
                      " with query:{query}".format(metric=metric,
                                                   query=query))

    def wait_for_statistic_of_metric(self, meter_name, query=None,
                                     period=None):
        """
        The method is a customization of test.status_timeout().
        """

        def check_status():
            stat_state_resp = self.ceilometer_client.statistics.list(
                meter_name, q=query, period=period)
            if len(stat_state_resp) > 0:
                return True  # All good.
            LOG.debug("Waiting for while metrics will available.")

        if not fuel_health.test.call_until_true(check_status, 600, 10):

            self.fail("Timed out waiting to become alarm")
        else:
            return self.ceilometer_client.statistics.list(meter_name, q=query,
                                                          period=period)

    def wait_notifications(self, notification_list, query):
        for sample in notification_list:
            self.wait_for_sample_of_metric(sample, query)

    @classmethod
    def _clean(cls, items, client):
        if items:
            for item in items[:]:
                try:
                    client.delete(item)
                    items.remove(item)
                except RuntimeError as exc:
                    cls.error_msg.append(exc)
                    LOG.debug(traceback.format_exc())

    @classmethod
    def _clean_alarms(cls):
        cls._clean(cls.alarm_id_list, cls.ceilometer_client.alarms)

    @classmethod
    def tearDownClass(cls):
        if cls.manager.clients_initialized:
            try:
                cls._clean_alarms()
            except Exception as exc:
                LOG.debug(exc)
        super(CeilometerBaseTest, cls).tearDownClass()
