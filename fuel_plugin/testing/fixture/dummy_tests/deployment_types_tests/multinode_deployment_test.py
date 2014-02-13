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
    "id": "multinode_deployment_test",
    "driver": "nose",
    "test_path": ("fuel_plugin/tests/functional/deployment_types_tests/"
                  "multinode_deployment.py"),
    "description": "Fake tests for multinode deployment on ubuntu",
    "deployment_tags": ["multinode", "ubuntu"],
    "test_runs_ordering_priority": 4,
    "exclusive_testsets": []
}

import unittest


class MultinodeTest(unittest.TestCase):

    def test_multi_novanet_depl(self):
        """fake empty test
       This is fake empty test
       for multinode on ubuntu with
       nova-network deployment
       Duration: 0sec
       Deployment tags: multinode, ubuntu, nova_network
        """
        self.assertTrue(True)

    def test_multi_quantum_depl(self):
        """fake empty test
        This is fake empty test
        for multinode on ubuntu with
        quatum deployment
        Duration: 0sec
        Deployment tags: multinode, ubuntu, quantum
        """
        self.assertTrue(True)

    def test_multi_depl(self):
        """fake empty test
        This is fake empty test
        for mutlinode on ubuntu
        deployment
        Duration: 1sec
        """
        self.assertTrue(True)
