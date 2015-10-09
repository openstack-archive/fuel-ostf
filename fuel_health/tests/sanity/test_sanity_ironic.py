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
from fuel_health import ironicmanager
from fuel_health import test

LOG = logging.getLogger(__name__)


class IronicSmokeTests(ironicmanager.IronicTest):
    """TestClass contains tests to check that Ironic nodes are operable

    Special requirements:
        1. A controller's IP address should be specified.
        2. An ironic-conductor's IP address should be specified.
        3. SSH user credentials for the controller and the ironic-conductor
           should be specified in the controller_node_ssh_user parameter
    """

    @classmethod
    def setUpClass(cls):
        super(IronicSmokeTests, cls).setUpClass()
        cls.controllers = cls.config.compute.online_controllers
        cls.conductors = cls.config.ironic.online_conductors

    @classmethod
    def tearDownClass(cls):
        pass

    def test_001_ironic_services(self):
        """Check that Ironic services are running
        Target component: Ironic

        Scenario:
            1. List services on Controller nodes.
            2. Check that ironic-api service is running.
            3. List services on Ironic Conductor nodes.
            4. Check that ironic-conductor service is running.
        Duration: 60 s.
        Deployment tags: Ironic
        Available since release: 2015.1.0-8.0
        """

        # Step 1
        expected = u'/usr/bin/ironic-api'
        cmd = 'pgrep -la ironic-api'
        # Step 2
        test.call_until_true(self.check_service_availability, 10, 30,
                             self.controllers, cmd, expected, 2, 60,
                             'ironic-api service is not running.')
        # Step 3
        expected = u'/usr/bin/ironic-conductor'
        cmd = 'pgrep -la ironic'
        # Step 4
        test.call_until_true(self.check_service_availability, 10, 30,
                             self.conductors, cmd, expected, 2, 60,
                             'ironic-conductor service is not running.')

    def test_002_ironic_node_actions(self):
        """Check that Ironic can operate nodes
        Target component: Ironic

        Scenario:
            1. Create Ironic node with fake driver.
            2. Update Ironic node properties.
            3. Show and check updated node properties.
            4. Delete Ironic node.
        Duration: 60 s.
        Deployment tags: Ironic
        Available since release: 2015.1.0-8.0
        """
        # Step 1
        fail_msg = ("Error creating node. Please refer to Openstack logs "
                    "for more information.")
        self.node = self.verify(20, self.node_create, 1, fail_msg,
                                'Node creation', driver='fake')
        LOG.debug(self.node)
        # Step 2
        prop = rand_name("ostf-prop")
        value_prop = rand_name("prop-value")
        fail_msg = ("Can't update node with properties. Please refer to "
                    "Openstack logs for more information.")
        self.node = self.verify(20, self.node_update, 2, fail_msg,
                                'Updating node', self.node, prop, value_prop)
        LOG.debug(self.node)
        # Step 3
        fail_msg = ("Can't show node properties. Please refer to "
                    "Openstack logs for more information.")
        self.node = self.verify(20, self.node_show, 3, fail_msg,
                                'Showing node', self.node, prop, value_prop)
        LOG.debug(self.node)
        # Step 4
        fail_msg = ("Can't delete node. Please refer to Openstack logs "
                    "for more information.")
        self.verify(20, self.node_delete, 4, fail_msg, 'Deleting node',
                    self.node)

    def test_003_ironic_list_entities(self):
        """List Ironic entities
        Target component: Ironic

        Scenario:
            1. List chassis.
            2. List drivers.
            3. List nodes.
            4. List ports.
        Duration: 80 s.
        Deployment tags: Ironic
        Available since release: 2015.1.0-8.0
        """
        fail_msg = ("Can't list chassis. Please refer to Openstack logs "
                    "for more information.")
        self.verify(20, self.list_chassis, 1, fail_msg, 'Chassis list')

        fail_msg = ("Can't list drivers. Please refer to Openstack logs "
                    "for more information.")
        self.verify(20, self.list_drivers, 2, fail_msg, 'Drivers list')

        fail_msg = ("Can't list chassis. Please refer to Openstack logs "
                    "for more information.")
        self.verify(20, self.list_nodes(), 3, fail_msg, 'Nodes list')

        fail_msg = ("Can't list ports. Please refer to Openstack logs "
                    "for more information.")
        self.verify(20, self.list_ports(), 4, fail_msg, 'Ports list')

