# Copyright 2015 Mirantis, Inc.
# All Rights Reserved.
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

import json
import logging
import requests

import fuel_health.common.ssh
from fuel_health.common.utils.data_utils import rand_name
import fuel_health.nmanager
import fuel_health.test


LOG = logging.getLogger(__name__)


class GlanceTest(fuel_health.nmanager.NovaNetworkScenarioTest):
    """Manager that provides access to the Glance python client for
    calling Glance API.
    """

    @classmethod
    def setUpClass(cls):
        super(GlanceTest, cls).setUpClass()
        cls.image_url = ('http://download.cirros-cloud.net/0.3.3/'
                         'cirros-0.3.3-x86_64-disk.img')
        cls.images = []
        if cls.manager.clients_initialized:
            if not cls.glance_client_v1:
                LOG.warning('Glance client v1 was not initialized')
            if not cls.glance_client:
                LOG.warning('Glance client v2 was not initialized')
            if not cls.glance_client_v1 and not cls.glance_client:
                cls.fail('Glance client v1 and v2 was not initialized')

    def tearDown(self):
        LOG.debug("Deleting images created by Glance test")
        self._clean_images()
        super(GlanceTest, self).tearDown()

    def _list_images(self, client):
        return client.images.list()

    def check_image_exists_in_network(self):
        resp = requests.head(self.image_url, allow_redirects=True)
        if not resp.ok:
            self.fail("Image not available in network.")

    def image_create(self, client, **kwargs):
        container_format = 'bare'
        copy_from = self.image_url
        disk_format = 'qcow2'
        image_name = rand_name('ostf_test-image_glance-')
        if client == self.glance_client_v1:
            image = client.images.create(name=image_name,
                                         container_format=container_format,
                                         copy_from=copy_from,
                                         disk_format=disk_format, **kwargs)
            self.images.append(image)
            return image
        elif client == self.glance_client:
            # TODO(vryzhenkin): Rework this function using Glance Tasks v2,
            # TODO(vryzhenkin) when Tasks will be supported by OpenStack Glance
            image = client.images.create(name=image_name,
                                         container_format=container_format,
                                         disk_format=disk_format, **kwargs)
            client.images.upload(image.id, 'dummy_data')
            self.images.append(image)
            return image

    def find_image_by_id(self, client, image_id):
        return client.images.get(image_id)

    def delete_image(self, client, object):
        return client.images.delete(object)

    def check_image_status(self, client, image, status='active'):
        def image_status_comparison():
            if self.find_image_by_id(client, image.id).status == status:
                return True

        if fuel_health.test.call_until_true(image_status_comparison, 120, 5):
            return self.find_image_by_id(client, image.id)
        else:
            self.fail('Image has incorrect status {0}'
                      .format(self.find_image_by_id(client, image.id)))

    def update_image(self, client, object, group_props, prop, value_prop):
        if client == self.glance_client_v1:
            properties = {group_props: {prop: value_prop}}
            return client.images.update(object, properties=properties)
        elif client == self.glance_client:
            properties = '{0}: {1}'.format(prop, value_prop)
            return client.images.update(object, group_props=properties)

    def find_props(self, client, object, group_props, prop, value_prop):
        msg = 'Can not find created properties in image'
        if client == self.glance_client_v1:
            for group in object.properties:
                if group == group_props:
                    for i in json.loads(object.properties[group]):
                        k = json.loads(object.properties[group])[prop]
                        if i == prop and k == unicode(value_prop):
                            return 'OK'
                        else:
                            self.fail(msg)
                else:
                    self.fail(msg)
        elif client == self.glance_client:
            properties = '{0}: {1}'.format(prop, value_prop)
            for key in object:
                if object[key] == properties:
                    return 'OK'
            self.fail(msg)
