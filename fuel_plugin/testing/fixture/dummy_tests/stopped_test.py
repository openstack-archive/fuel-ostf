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
    "id": "stopped_test",
    "driver": "nose",
    "test_path": "fuel_plugin/tests/functional/dummy_tests/stopped_test.py",
    "description": "Long running 25 secs fake tests",
    "deployment_tags": [],
    "test_runs_ordering_priority": 2,
    "exclusive_testsets": []
}

import time
import unittest


class dummy_tests_stopped(unittest.TestCase):

    def test_really_long(self):
        """This is long running tests
           Duration: 25sec
        """
        time.sleep(25)
        self.assertTrue(True)

    def test_one_no_so_long(self):
        """What i am doing here? You ask me????
        """
        time.sleep(5)
        self.assertFalse(1 == 2)

    def test_not_long_at_all(self):
        """You know.. for testing
            Duration: 1sec
        """
        self.assertTrue(True)
