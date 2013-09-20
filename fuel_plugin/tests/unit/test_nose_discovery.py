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

from mock import patch
import unittest2
from fuel_plugin.ostf_adapter.nose_plugin import nose_discovery


from fuel_plugin.ostf_adapter.storage import models


stopped__profile__ = {
    "id": "stopped_test",
    "driver": "nose",
    "test_path": "functional/dummy_tests/stopped_test.py",
    "description": "Long running 25 secs fake tests"
}
general__profile__ = {
    "id": "general_test",
    "driver": "nose",
    "test_path": "functional/dummy_tests/general_test.py",
    "description": "General fake tests"
}


@patch('fuel_plugin.ostf_adapter.nose_plugin.nose_discovery.engine')
class TestNoseDiscovery(unittest2.TestCase):

    def setUp(self):
        self.fixtures = [models.TestSet(**stopped__profile__),
                         models.TestSet(**general__profile__)]
        self.fixtures_iter = iter(self.fixtures)

    def test_discovery(self, engine):
        engine.get_session().merge.return_value = \
            lambda *args, **kwargs: self.fixtures_iter.next()
        nose_discovery.discovery(path='functional/dummy_tests')
        self.assertEqual(engine.get_session().merge.call_count, 2)
