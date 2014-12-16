# Copyright 2014 Mirantis, Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import logging

from fuel_health.common.utils.data_utils import rand_name
import fuel_health.nmanager
import fuel_health.test
import fuel_health.common.ssh


LOG = logging.getLogger(__name__)


class GlanceTest(fuel_health.nmanager.NovaNetworkScenarioTest):
    """
    Manager that provides access to the Glance python client for
    calling Glance API.
    """

    @classmethod
    def setUpClass(cls):
        super(GlanceTest, cls).setUpClass()
        cls.images = []
        if cls.manager.clients_initialized:
            if not cls.glance_client:
                LOG.warning('Glance client v1 was not initialized')
            if not cls.glance_client_v2:
                LOG.warning('Glance client v2 was not initialized')
            if not cls.glance_client and not cls.glance_client_v2:
                cls.fail('Glance client v1 and v2 was not initialized')

    def tearDown(self):
        LOG.debug("Deleting images created by Glance test")
        self._clean_images()
        super(GlanceTest, self).tearDown()

    @staticmethod
    def _list_images(client):
        return client.images.list()

    def image_create(self, client, **kwargs):
        container_format = 'bare'
        location = 'http://download.cirros-cloud.net/0.3.3/' \
                   'cirros-0.3.3-x86_64-disk.img'
        disk_format = 'qcow2'
        image_name = rand_name('ostf_test-image_glance-')
        image = client.images.create(name=image_name,
                                     container_format=container_format,
                                     location=location,
                                     disk_format=disk_format, **kwargs)
        self.images.append(image)
        return image

    def find_image_by_id(self, client, image_id):
        image = client.images.get(image_id)
        return image

    def delete_image_by_id(self, client, object):
        return client.images.delete(object)


