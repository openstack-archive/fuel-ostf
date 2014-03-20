#    Copyright 2014 Mirantis, Inc.
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
    "id": "gemini_second",
    "driver": "nose",
    "test_path": ("fuel_plugin/tests/functional/"
                  "dummy_tests/dependent_testsets/gemini_second.py"),
    "description": "Intersects with gemini_first testset",
    "deployment_tags": ["dependent_tests"],
    "test_runs_ordering_priority": 11,
    "exclusive_testsets": ["gemini_first"]
}

import time
import unittest2


class TestGeminiSecond(unittest2.TestCase):
    def test_fake_long_succes_gs(self):
        time.sleep(30)
        self.assertTrue(True)

    def test_fake_quick_success_gs(self):
        self.assertTrue(True)
