#    Copyright 2016 Mirantis, Inc.
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
    "id": "murano_test_tags",
    "driver": "nose",
    "test_path": ("fuel_plugin/tests/functional/dummy_tests/"
                  "deployment_types_tests/murano_plugin_depl_tags.py"),
    "description": "Fake testset to test murano plugin deployment tags",
    "deployment_tags": ["murano_plugin | murano"],
    "test_runs_ordering_priority": 5,
    "exclusive_testsets": []
}

import unittest


class MuranoDeplTagsTests(unittest.TestCase):

    def test_murano_plugin_tag(self):
        """fake empty test
        This is fake empty test with
        example of description of alternative
        deployment tags
        Deployment tags: murano_plugin
        """
        self.assertTrue(True)

    def test_murano_tag(self):
        """fake empty test
        This is fake empty test with
        example of description of alternative
        deployment tags
        Deployment tags: murano
        """
        self.assertTrue(True)

    def test_murano_or_plugin_tag(self):
        """fake empty test
        This is fake empty test with
        example of description of alternative
        deployment tags
        Deployment tags: murano | murano_plugin
        """
        self.assertTrue(True)