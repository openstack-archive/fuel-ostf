# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Mirantis, Inc.
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

from fuel_health import glance

LOG = logging.getLogger(__name__)


class GlanceSmokeTests(glance.GlanceTest):
    """
    Test suite verifies:
    - image creation
    - image deletion
    """

    def test_create_and_delete_image(self):
        """Check that user can create and delete image
        Target component: Glance

        Scenario:
            1.Create image
            2.Check that image created successfully
            3.Delete image
        Duration: 90 s.
        """
        fail_msg = "Error creating image. Please refer to logs."
        self.image = self.verify(60, self.image_create, 1, fail_msg,
                                 'Image creation', self.glance_client)

        fail_msg = "Image don't appear at list. Please refer to logs"
        self.verify(10, self.find_image_by_id, 2, fail_msg, 'Finding image',
                    self.glance_client, self.image.id)

        fail_msg = 'Cant delete image. Please refer to logs.'
        self.verify(20, self.delete_image_by_id, 3, fail_msg, 'Deleting image',
                    self.glance_client, self.image.id)