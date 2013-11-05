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

from mock import patch, Mock
import unittest2
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from fuel_plugin.ostf_adapter.nose_plugin import nose_discovery
from fuel_plugin.ostf_adapter.storage import models

TEST_PATH = 'fuel_plugin/tests/functional/dummy_tests'


class TransactionBeginMock:
    def __init__(inst, subtransactions):
        pass

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        pass


class TestNoseDiscovery(unittest2.TestCase):

    def setUp(self):
        self.session_mock = Mock()
        self.session_mock.begin = TransactionBeginMock
        self.session_mock.test_attr = 'hello'

    def test_discovery(self):
        expected = {
            'test_sets_count': 6,
            'tests_count': 20
        }

        self.session_mock.test_attr = 'hello!'
        nose_discovery.discovery(
            path=TEST_PATH,
            session=self.session_mock
        )

        test_sets = [
            el[0][0] for el in self.session_mock.merge.call_args_list
            if isinstance(el[0][0], models.TestSet)
        ]

        tests = [
            el[0][0] for el in self.session_mock.merge.call_args_list
            if isinstance(el[0][0], models.Test)
        ]

        self.assertTrue(
            all(
                [len(test_sets) == expected['test_sets_count'],
                 len(tests) == expected['tests_count']]
            )
        )

        unique_test_sets = list(set([testset.id for testset in test_sets]))
        unique_tests = list(set([test.name for test in tests]))

        self.assertTrue(
            all(
                [len(unique_test_sets) == len(test_sets),
                 len(unique_tests) == len(tests)]
            )
        )

    def test_get_proper_description(self):
        expected = {
            'title': 'fake empty test',
            'name': ('fuel_plugin.tests.functional.'
                     'dummy_tests.deployment_types_tests.'
                     'ha_deployment_test.HATest.test_ha_rhel_depl'),
            'duration': '0sec',
            'test_set_id': 'ha_deployment_test',
            'deployment_tags': ['ha', 'rhel']

        }

        nose_discovery.discovery(
            path=TEST_PATH,
            session=self.session_mock
        )

        tests = [
            el[0][0] for el in self.session_mock.merge.call_args_list
            if isinstance(el[0][0], models.Test)
        ]

        test = [t for t in tests if t.name == expected['name']].pop()

        self.assertTrue(
            all(
                [
                    expected[key] == getattr(test, key)
                    for key in expected.keys()
                ]
            )
        )

    def test_discovery_tests_with_alternative_depl_tags(self):
        expected = {
            'testset': {
                'id': 'alternative_depl_tags_test',
                'deployment_tags': ['alternative | alternative_test']
            },
            'test': {
                'name': ('fuel_plugin.tests.functional.dummy_tests.'
                         'deployment_types_tests.alternative_depl_tags_test.'
                         'AlternativeDeplTagsTests.test_simple_fake_test'),
                'deployment_tags': ['one_tag| another_tag', 'other_tag']
            }
        }

        nose_discovery.discovery(
            path=TEST_PATH,
            session=self.session_mock
        )

        test_sets = [
            el[0][0] for el in self.session_mock.merge.call_args_list
            if isinstance(el[0][0], models.TestSet)
        ]

        tests = [
            el[0][0] for el in self.session_mock.merge.call_args_list
            if isinstance(el[0][0], models.Test)
        ]

        needed_testset = [testset for testset in test_sets
                          if testset.id == expected['testset']['id']].pop()

        needed_test = [test for test in tests
                       if test.name == expected['test']['name']].pop()

        self.assertEqual(
            needed_testset.deployment_tags,
            expected['testset']['deployment_tags']
        )

        self.assertEqual(
            needed_test.deployment_tags,
            expected['test']['deployment_tags']
        )
