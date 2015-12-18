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
    "id": "general_test",
    "driver": "nose",
    "test_path": "fuel_plugin/tests/functional/dummy_tests/general_test.py",
    "description": "General fake tests",
    "deployment_tags": [],
    "test_runs_ordering_priority": 1,
    "exclusive_testsets": []
}

import httplib
import time
import unittest2


class DummyTest(unittest2.TestCase):
    """Class docstring is required?
    """

    def test_fast_pass(self):
        """fast pass test
        This is a simple always pass test
        Duration: 1sec
        """
        self.assertTrue(True)

    def test_long_pass(self):
        """Will sleep 5 sec
        This is a simple test
        it will run for 5 sec
        Duration: 5sec
        """
        time.sleep(5)
        self.assertTrue(True)

    def test_fast_fail(self):
        """Fast fail
        """
        self.assertTrue(False, msg='Something goes wroooong')

    def test_fast_error(self):
        """And fast error
        """
        conn = httplib.HTTPSConnection('random.random/random')
        conn.request("GET", "/random.aspx")

    def test_fail_with_step(self):
        """Fast fail with step
        """
        self.fail('Step 3 Failed: Fake fail message')

    def test_skip(self):
        """Skip
        """
        msg = 'The reason to skip goes here'
        self.skipTest(msg)

    def test_skip_directly(self):
        """Skip with exception
        """
        msg = 'Nothing to see here'
        raise unittest2.SkipTest(msg)
