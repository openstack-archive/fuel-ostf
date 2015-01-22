#    Copyright 2015 Mirantis, Inc.
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
    "id": "test_versioning",
    "driver": "nose",
    "test_path": "fuel_plugin/tests/functional/dummy_tests/test_versioning.py",
    "description": "Test suite that contains fake tests for versioning check",
    "deployment_tags": ["releases_comparison"],
    "test_runs_ordering_priority": 13,
    "exclusive_testsets": [],
    "available_since_release": "2015.2-6.0",
}

import unittest2


class TestVersioning(unittest2.TestCase):
    def test_simple_fake_first(self):
        """This is simple fake test
        for versioning checking.
        It should be discovered for
        releases == of >= 2015.2-6.0
        Available since release: 2015.2-6.0
        Deployment tags: releases_comparison
        """
        self.assertTrue(True)

    def test_simple_fake_second(self):
        """This is simple fake test
        for versioning checking.
        It should be discovered for
        releases == of >= 2015.2-6.1
        Available since release: 2015.2-6.1
        Deployment tags: releases_comparison
        """
        self.assertTrue(True)
