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

from fuel_health import glancemanager

LOG = logging.getLogger(__name__)


class GlanceSanityTests(glancemanager.GlanceTest):
    """GlanceSanityTests contains verifications of basic Glance functionality.
    """

    def test_glance_image_list(self):
        """Request image list using Glance v1
        Target component: Glance

        Scenario
                1. Get image list using Glance
                2. Confirm that a response is received

        Duration: 10 s.
        Available since release: 2014.2-6.1
        """

        fail_msg = "Can't get list of images. Glance API isn't available. "
        image_list_resp = self.verify(10, self._list_images,
                                      1, fail_msg, "image listing",
                                      self.glance_client_v1)

        fail_msg = ("Image list is unavailable. Please refer to "
                    "OSTF logs for more information")
        self.verify_response_true(image_list_resp, fail_msg, 2)

    def test_glance_image_list_v2(self):
        """Request image list using Glance v2
        Target component: Glance

        Scenario
                1. Get image list using Glance
                2. Confirm that a response is received

        Duration: 10 s.
        Available since release: 2014.2-6.1
        """

        fail_msg = "Can't get list of images. Glance API isn't available. "
        image_list_resp = self.verify(10, self._list_images,
                                      1, fail_msg, "image listing",
                                      self.glance_client)

        fail_msg = ("Image list is unavailable. Please refer to "
                    "OSTF logs for more information")
        self.verify_response_true(image_list_resp, fail_msg, 2)
