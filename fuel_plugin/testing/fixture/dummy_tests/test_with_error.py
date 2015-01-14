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
    "id": "test_with_error",
    "driver": "nose",
    "test_path": "fuel_plugin/tests/functional/dummy_tests/test_with_error.py",
    "description": "Test that introduces error while setting up",
    "deployment_tags": ['test_error'],
    "test_runs_ordering_priority": 6,
    "exclusive_testsets": []
}

import unittest


class FakeTests(unittest.TestCase):

    def test_successfully_passed(self):
        """imitation of work
        """
        self.assertTrue(True)


class WithErrorTest(unittest.TestCase):
    """This is supoused to introduce errorness behaviour
    in means that it have exception raised in setUp method for
    testing purposes.
    """
    @classmethod
    def setUpClass(cls):
        raise Exception('Unhandled exception in setUpClass')

    def setUp(self):
        raise Exception('Error in setUp method')

    def test_supposed_to_be_success(self):
        """test in errorness class
        """
        self.assertTrue(True)

    def test_supposed_to_be_fail(self):
        self.assertFalse(False)
