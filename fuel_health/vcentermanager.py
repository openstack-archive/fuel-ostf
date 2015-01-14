#!/usr/bin/env python
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
import traceback

from fuel_health.common.utils.data_utils import rand_name
import fuel_health.nmanager
import fuel_health.test

LOG = logging.getLogger(__name__)


class vCenterTest(fuel_health.nmanager.NovaNetworkScenarioTest):
    """
    Manager that tests vCenter functionality.
    """

    @classmethod
    def setUpClass(self):
        super(vCenterTest, self).setUpClass()
        if self.manager.clients_initialized:
            self.manager.config.compute.image_name = 'TestVM-vmdk'

    def setUp(self):
        super(vCenterTest, self).setUp()
        self.env_name = rand_name('ostf_test-vCenter_env')

        # If there are no 'compute-vcenter' nodes
        if not self.compute.vcenter_nodes \
                and self.config.compute.libvirt_type != 'vcenter':
            self.skipTest('There are no "compute-vcenter" nodes')

    def tearDown(self):
        """
        This method allows to clean up the OpenStack environment
        after the vCenter OSTF tests.
        """

        for env in self.list_environments()["environments"]:
            if self.env_name in env["name"]:
                try:
                    self.delete_environment(env["id"])
                except:
                    LOG.warning(traceback.format_exc())

        super(vCenterTest, self).tearDown()
