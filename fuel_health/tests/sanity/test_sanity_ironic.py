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

LOG = logging.getLogger(__name__)


class IronicSanityTests(ironicmanager.IronicTest):
    """TestClass contains tests to check that Ironic nodes are operable

    Special requirements:
        1. A controller's IP address should be specified.
        2. An ironic-conductor's IP address should be specified.
        3. SSH user credentials for the controller and the ironic-conductor
           should be specified in the controller_node_ssh_user parameter
    """

    @classmethod
    def setUpClass(cls):
        super(IronicSanityTests, cls).setUpClass()
        cls.controllers = cls.config.compute.online_controllers
        cls.conductors = cls.config.ironic.online_conductors
        if not cls.controllers:
            cls.skipTest('There are no Controller nodes.')
        if not cls.conductors:
            cls.skipTest('There are no Ironic Conductor nodes.')

    def test_001_ironic_services(self):
        """Check that Ironic services are running
        Target component: Ironic

        Scenario:
            1. Check that ironic-api service is running on controller node.
            2. Check that ironic-conductor service is running on Ironic node.
            3. Check that nova-compute service is running on controller node.
        Duration: 60 s.
        Deployment tags: Ironic
        Available since release: liberty-9.0
        """

        # Step 1
        expected = u'/usr/bin/ironic-api'
        cmd = 'pgrep -la ironic-api'
        fail_msg = 'Ironic-api service is not running.'
        action = 'checking ironic-api service'
        self.verify(60, self.check_service_availability, 1, fail_msg, action,
                    self.controllers, cmd, expected)
        # Step 2
        expected = u'/usr/bin/ironic-conductor'
        cmd = 'pgrep -la ironic'
        fail_msg = 'Ironic-conductor service is not running.'
        action = 'checking ironic-conductor service'
        self.verify(60, self.check_service_availability, 2, fail_msg, action,
                    self.conductors, cmd, expected)
        # Step 3
        expected = u'/usr/bin/nova-compute'
        cmd = 'pgrep -la nova-compute'
        fail_msg = 'Nova-compute service is not running.'
        action = 'checking nova-compute service'
        self.verify(60, self.check_service_availability, 3, fail_msg, action,
                    self.controllers, cmd, expected)

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
        Available since release: liberty-9.0
        """
        # Step 1
        fail_msg = "Error creating node."
        self.node = self.verify(20, self.node_create, 1, fail_msg,
                                'Node creation', driver='fake',
                                extra={'NodeTest': ''})
        LOG.debug(self.node)
        # Step 2
        prop = rand_name("ostf-prop")
        value_prop = rand_name("prop-value")
        fail_msg = "Can't update node with properties."
        self.node = self.verify(20, self.node_update, 2, fail_msg,
                                'Updating node', self.node, prop, value_prop)
        LOG.debug(self.node)
        # Step 3
        fail_msg = "Can't show node properties."
        self.node = self.verify(20, self.node_show, 3, fail_msg,
                                'Showing node', self.node)
        LOG.debug(self.node)
        for p, v in self.node.properties.items():
            self.verify(5, self.assertTrue, 3, "Can't check node property.",
                        'Checking node property', prop in p)
            self.verify(5, self.assertTrue, 3, "Can't check property value.",
                        'Checking property value', value_prop in v)
        # Step 4
        fail_msg = "Can't delete node."
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
        Available since release: liberty-9.0
        """
        fail_msg = "Can't list chassis."
        self.verify(20, self.list_chassis, 1, fail_msg, 'Chassis list')

        fail_msg = "Can't list drivers."
        self.drivers = self.verify(20, self.list_drivers, 2,
                                   fail_msg, 'Drivers list')
        LOG.debug(self.drivers)
        self.wanted_drivers = {u'fake', u'fuel_ssh',
                               u'fuel_ipmitool', u'fuel_libvirt'}
        for driver in self.wanted_drivers:
            self.verify(20, self.get_driver, 2, "Can't find driver.",
                        'Checking drivers in list', driver)

        fail_msg = "Can't list nodes."
        self.verify(20, self.list_nodes, 3, fail_msg, 'Nodes list')

        fail_msg = "Can't list ports."
        self.verify(20, self.list_ports, 4, fail_msg, 'Ports list')
