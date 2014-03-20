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
    "id": "alternative_depl_tags_test",
    "driver": "nose",
    "test_path": ("fuel_plugin/tests/functional/dummy_tests/"
                  "deployment_types_tests/alternative_depl_tags_test.py"),
    "description": "Fake testset to test alternative deployment tags",
    "deployment_tags": ["alternative | alternative_test"],
    "test_runs_ordering_priority": 5
}

import unittest


class AlternativeDeplTagsTests(unittest.TestCase):

    def test_simple_fake_test(self):
        """fake empty test
        This is fake empty test with
        example of description of alternative
        deployment tags
        Deployment tags: one_tag| another_tag, other_tag
        """
        self.assertTrue(True)
