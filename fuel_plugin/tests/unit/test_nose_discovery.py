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

import unittest2
from mock import patch
from fuel_plugin.ostf_adapter.nose_plugin import nose_discovery


from fuel_plugin.ostf_adapter.storage import models


stopped__profile__ = {
    "id": "stopped_test",
    "driver": "nose",
    "test_path": "fuel_plugin/tests/functional/dummy_tests/stopped_test.py",
    "description": "Long running 25 secs fake tests"
}
general__profile__ = {
    "id": "general_test",
    "driver": "nose",
    "test_path": "fuel_plugin/tests/functional/dummy_tests/general_test.py",
    "description": "General fake tests"
}


@patch('fuel_plugin.ostf_adapter.nose_plugin.nose_discovery.engine')
class TestNoseDiscovery(unittest2.TestCase):

    def setUp(self):
        self.fixtures = [models.TestSet(**general__profile__),
                         models.TestSet(**stopped__profile__)]

        self.fixtures_iter = iter(self.fixtures)

    def test_discovery(self, engine):
        engine.get_session().merge.side_effect = \
            lambda *args, **kwargs: self.fixtures_iter.next()

        nose_discovery.discovery(
            path='fuel_plugin/tests/functional/dummy_tests'
        )

        self.assertEqual(engine.get_session().merge.call_count, 2)

    def test_get_proper_description(self, engine):
        '''
        Checks whether retrived docsctrings from tests
        are correct (in this occasion -- full).

        Magic that is used here is based on using
        data that is stored deeply in passed to test
        method mock object.
        '''
        #etalon data is list of docstrings of tests
        #of particular test set
        expected = {
            'title': 'fast pass test',
            'name':
                'fuel_plugin.tests.functional.dummy_tests.general_test.Dummy_test.test_fast_pass',
            'duration': '1sec',
            'description':
                '        This is a simple always pass test\n        '
        }

        #mocking behaviour of afterImport hook from DiscoveryPlugin
        #so that another hook -- addSuccess could process data properly
        engine.get_session().merge = lambda arg: arg

        #following code provide mocking logic for
        #addSuccess hook from DiscoveryPlugin that
        #(mentioned logic) in turn allows us to
        #capture data about test object that are processed
        engine.get_session()\
              .query()\
              .filter_by()\
              .update\
              .return_value = None

        nose_discovery.discovery(
            path='fuel_plugin/tests/functional/dummy_tests'
        )

        #now we can refer to captured test objects (not test_sets) in order to
        #make test comparison against etalon
        test_obj_to_compare = [
            call[0][0] for call in engine.get_session().add.call_args_list
            if (
                isinstance(call[0][0], models.Test)
                and
                call[0][0].name.rsplit('.')[-1] == 'test_fast_pass'
            )
        ][0]

        self.assertTrue(
            all(
                [
                    expected[key] == test_obj_to_compare.__dict__[key]
                    for key in expected.keys()
                ]
            )
        )
