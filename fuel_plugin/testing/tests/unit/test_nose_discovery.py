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

from mock import Mock

from fuel_plugin.ostf_adapter.nose_plugin import nose_discovery
from fuel_plugin.ostf_adapter.storage import models
from fuel_plugin.testing.tests import base

TEST_PATH = 'fuel_plugin/testing/fixture/dummy_tests'


class TransactionBeginMock:
    def __init__(inst, subtransactions):
        pass

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        pass


class TestNoseDiscovery(base.BaseUnitTest):

    @classmethod
    def setUpClass(cls):
        session_mock = Mock()
        session_mock.begin = TransactionBeginMock

        nose_discovery.discovery(
            path=TEST_PATH,
            session=session_mock
        )

        cls.test_sets = [
            el[0][0] for el in session_mock.merge.call_args_list
            if isinstance(el[0][0], models.TestSet)
        ]

        cls.tests = [
            el[0][0] for el in session_mock.merge.call_args_list
            if isinstance(el[0][0], models.Test)
        ]

    def _find_needed_test(self, test_name):
        return next(t for t in self.tests if t.name == test_name)

    def _find_needed_test_set(self, test_set_id):
        return next(t for t in self.test_sets if t.id == test_set_id)

    def test_discovery(self):
        expected = {
            'test_sets_count': 10,
            'tests_count': 29
        }

        self.assertTrue(
            all(
                [len(self.test_sets) == expected['test_sets_count'],
                 len(self.tests) == expected['tests_count']]
            )
        )

        unique_test_sets = list(
            set([testset.id for testset in self.test_sets])
        )
        unique_tests = list(set([test.name for test in self.tests]))

        self.assertTrue(
            all(
                [len(unique_test_sets) == len(self.test_sets),
                 len(unique_tests) == len(self.tests)]
            )
        )

    def test_get_proper_description(self):
        expected = {
            'title': 'fake empty test',
            'name': ('fuel_plugin.testing.fixture.'
                     'dummy_tests.deployment_types_tests.'
                     'ha_deployment_test.HATest.test_ha_rhel_depl'),
            'duration': '0sec',
            'test_set_id': 'ha_deployment_test',
            'deployment_tags': ['ha', 'rhel']

        }

        test = [t for t in self.tests if t.name == expected['name']][0]

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
                'name': ('fuel_plugin.testing.fixture.dummy_tests.'
                         'deployment_types_tests.alternative_depl_tags_test.'
                         'AlternativeDeplTagsTests.test_simple_fake_test'),
                'deployment_tags': ['one_tag| another_tag', 'other_tag']
            }
        }
        needed_testset = self._find_needed_test_set(expected['testset']['id'])

        needed_test = self._find_needed_test(expected['test']['name'])

        self.assertEqual(
            needed_testset.deployment_tags,
            expected['testset']['deployment_tags']
        )

        self.assertEqual(
            needed_test.deployment_tags,
            expected['test']['deployment_tags']
        )

    def test_if_test_belongs_to_test_set(self):
        test_set_id = 'ha'
        pass_checks = (
            'test_ha_sth',
            'test-ha-ha',
            'test.ha.sahara',
            'test.ha.sth',
        )
        fail_checks = (
            'test_sahara',
            'test.nonha.sth',
            'test.nonha.sahara',
        )

        for test_id in pass_checks:
            self.assertTrue(
                nose_discovery.DiscoveryPlugin.test_belongs_to_testset(
                    test_id, test_set_id)
            )

        for test_id in fail_checks:
            self.assertFalse(
                nose_discovery.DiscoveryPlugin.test_belongs_to_testset(
                    test_id, test_set_id)
            )

    def test_release_version_attribute(self):
        for test_entity in (self.tests, self.test_sets):
            self.assertTrue(
                all(
                    [hasattr(t, 'available_from_release') for t in test_entity]
                )
            )

        expected = {
            'test_set': {
                'id': 'test_versioning',
                'available_from_release': '2015.2-6.0',
            },
            'tests': [
                {'name': ('fuel_plugin.testing.fixture.dummy_tests.'
                          'test_versioning.TestVersioning.'
                          'test_simple_fake_first'),
                 'available_from_release': '2015.2-6.0', },
                {'name': ('fuel_plugin.testing.fixture.dummy_tests.'
                          'test_versioning.TestVersioning.'
                          'test_simple_fake_second'),
                 'available_from_release': '2015.2-6.1', },
            ]
        }

        needed_test_set = self._find_needed_test_set(
            expected['test_set']['id']
        )
        self.assertEqual(needed_test_set.available_from_release,
                         expected['test_set']['available_from_release'])

        for test in expected['tests']:
            needed_test = self._find_needed_test(test['name'])
            self.assertEqual(needed_test.available_from_release,
                             test['available_from_release'])
