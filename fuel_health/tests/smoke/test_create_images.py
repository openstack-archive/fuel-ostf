# Copyright 2015 Mirantis, Inc.
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
from fuel_health import glancemanager

LOG = logging.getLogger(__name__)


class GlanceSmokeTests(glancemanager.GlanceTest):
    """Test suite verifies:
    - image creation
    - image update
    - image deletion
    """

    def test_create_and_delete_image(self):
        """Check that user can create, update and delete image using Glance v1
        Target component: Glance

        Scenario:
            1.Checking Internet connection
            2.Checking that image exists in network storage
            3.Send request to create image via URL
            4.Checking image status
            5.Check that image was created successfully
            6.Update image with properties
            7.Check that properties was updated successfully
            8.Delete image

        Duration: 130 s.
        Available since release: 2014.2-6.1
        Deployment tags: Glance
        """
        fail_msg = "Internet connection error."
        self.verify(10, self._ping_ip_address, 1, fail_msg,
                    'Checking internet connection', "8.8.8.8", 10, (1, 5))

        fail_msg = "Cirros image is not available in public network storage."
        self.verify(5, self.check_image_exists_in_network, 2, fail_msg,
                    'Checking that image exists in network storage')

        fail_msg = ("Error creating image. Please refer to Openstack logs "
                    "for more information.")
        self.image = self.verify(5, self.image_create, 3, fail_msg,
                                 'Image creation', self.glance_client_v1)

        fail_msg = ("Image status is incorrect. Please refer to "
                    "Openstack logs for more information.")
        self.verify(100, self.check_image_status, 4, fail_msg,
                    'Checking image status', self.glance_client_v1, self.image)

        fail_msg = ("Image doesn't appear at list. Please refer to "
                    "Openstack logs for more information.")
        self.verify(10, self.find_image_by_id, 5, fail_msg, 'Finding image',
                    self.glance_client_v1, self.image.id)

        group_props = rand_name("ostf_test")
        prop = rand_name("ostf-prop")
        value_prop = rand_name("prop-value")

        fail_msg = ("Can't update image with properties. Please refer to "
                    "Openstack logs for more information.")
        self.verify(5, self.update_image, 6, fail_msg, 'Updating image',
                    self.glance_client_v1, self.image, group_props, prop,
                    value_prop)

        fail_msg = ("Can't find appended properties. Please refer to "
                    "OSTF logs for more information.")
        self.verify(5, self.find_props, 7, fail_msg, 'Finding properties',
                    self.glance_client_v1, self.image, group_props, prop,
                    value_prop)

        fail_msg = ("Cant delete image. Please refer to Openstack logs "
                    "for more information.")
        self.verify(10, self.delete_image, 8, fail_msg, 'Deleting image',
                    self.glance_client_v1, self.image)

    def test_create_and_delete_image_v2(self):
        """Check that user can create, update and delete image using Glance v2
        Target component: Glance

        Scenario:
            1.Send request to create image
            2.Checking image status
            3.Check that image was created successfully
            4.Update image with properties
            5.Check that properties was updated successfully
            6.Delete image

        Duration: 70 s.
        Available since release: 2014.2-6.1
        Deployment tags: Glance
        """
        fail_msg = ("Error creating image. Please refer to Openstack logs "
                    "for more information.")
        self.image = self.verify(10, self.image_create, 1, fail_msg,
                                 'Image creation', self.glance_client)

        fail_msg = ("Image status is incorrect. Please refer to "
                    "Openstack logs for more information.")
        self.verify(10, self.check_image_status, 2, fail_msg,
                    'Checking image status', self.glance_client, self.image)

        fail_msg = ("Image doesn't appear at list. Please refer to "
                    "Openstack logs for more information.")
        self.verify(10, self.find_image_by_id, 3, fail_msg, 'Finding image',
                    self.glance_client, self.image.id)

        group_props = rand_name("ostf_test")
        prop = rand_name("ostf-prop")
        value_prop = rand_name("prop-value")

        fail_msg = ("Can't update image with properties. Please refer to "
                    "Openstack logs for more information.")
        self.image = self.verify(10, self.update_image, 4, fail_msg,
                                 'Updating image', self.glance_client,
                                 self.image.id, group_props, prop, value_prop)

        fail_msg = ("Can't find appended properties. Please refer to "
                    "OSTF logs for more information.")
        self.verify(10, self.find_props, 5, fail_msg, 'Finding properties',
                    self.glance_client, self.image, group_props, prop,
                    value_prop)

        fail_msg = ("Cant delete image. Please refer to Openstack logs "
                    "for more information.")
        self.verify(20, self.delete_image, 5, fail_msg, 'Deleting image',
                    self.glance_client, self.image.id)
