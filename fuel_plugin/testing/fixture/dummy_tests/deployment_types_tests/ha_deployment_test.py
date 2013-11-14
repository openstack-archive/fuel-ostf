#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

__profile__ = {
    "id": "ha_deployment_test",
    "driver": "nose",
    "test_path": ("fuel_plugin/tests/functional/deployment_types_tests/"
                  "ha_deployment_test.py"),
    "description": "Fake tests for HA deployment",
    "deployment_tags": ["Ha"]
}

import unittest


class HATest(unittest.TestCase):

    def test_ha_rhel_depl(self):
        """fake empty test
        This is fake tests for ha
        rhel deployment
        Duration: 0sec
        Deployment tags: Ha, Rhel
        """
        self.assertTrue(True)

    def test_ha_rhel_quantum_depl(self):
        """fake empty test
        This is a fake test for
        ha rhel with quantum
        Duration: 0sec
        Deployment tags: ha, rhel, quantum
        """
        self.assertTrue(True)

    def test_ha_ubuntu_depl(self):
        """fake empty test
        This is fake test for ha
        ubuntu deployment
        Deployment tags: ha, ubuntu
        """
        self.assertTrue(True)

    def test_ha_ubuntu_novanet_depl(self):
        """fake empty test
        This is empty test for ha
        ubuntu with nova-network
        deployment
        Deployment tags: ha, ubuntu, nova_network
        """
        self.assertTrue(True)

    def test_ha_depl(self):
        """fake empty test
        This is empty test for any
        ha deployment
        """
        self.assertTrue(True)
