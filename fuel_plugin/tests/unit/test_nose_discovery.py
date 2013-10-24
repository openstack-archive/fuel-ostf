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
from mock import patch, Mock
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from fuel_plugin.ostf_adapter.nose_plugin import nose_discovery
from fuel_plugin.ostf_adapter.storage import models

TEST_PATH = 'fuel_plugin/tests/functional/dummy_tests'


class BaseTestNoseDiscovery(unittest2.TestCase):
    '''
    All test writing to database is wrapped in
    non-ORM transaction which is created in
    test_case setUp method and rollbacked in
    tearDown, so that keep prodaction base clean
    '''

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            'postgresql+psycopg2://ostf:ostf@localhost/ostf'
        )

        cls.Session = sessionmaker()

    def setUp(self):
        self.connection = self.engine.connect()
        self.trans = self.connection.begin()

        self.Session.configure(bind=self.connection)
        self.session = self.Session()

    def tearDown(self):
        self.trans.rollback()
        self.session.close()
        self.connection.close()


class TestNoseDiscovery(BaseTestNoseDiscovery):

    @classmethod
    def setUpClass(cls):
        super(TestNoseDiscovery, cls).setUpClass()

    def setUp(self):
        super(TestNoseDiscovery, self).setUp()

    def tearDown(self):
        super(TestNoseDiscovery, self).tearDown()

    def test_discovery(self):
        expected = {
            'test_sets_count': 6,
            'tests_count': 20
        }

        nose_discovery.discovery(
            path=TEST_PATH,
            session=self.session
        )

        test_sets_count = self.session.query(func.count('*'))\
            .select_from(models.TestSet)\
            .scalar()

        tests_count = self.session.query(func.count('*'))\
            .select_from(models.Test)\
            .scalar()

        self.assertTrue(
            all(
                [test_sets_count == expected['test_sets_count'],
                 tests_count == expected['tests_count']]
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
            session=self.session
        )

        test = self.session.query(models.Test)\
            .filter_by(name=expected['name'])\
            .filter_by(test_set_id=expected['test_set_id'])\
            .one()

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
            session=self.session
        )

        test_set = self.session.query(models.TestSet)\
            .filter_by(id=expected['testset']['id'])\
            .one()

        self.assertEqual(
            test_set.deployment_tags,
            expected['testset']['deployment_tags']
        )

        test = self.session.query(models.Test)\
            .filter_by(test_set_id=expected['testset']['id'])\
            .filter_by(name=expected['test']['name'])\
            .one()

        self.assertEqual(
            test.deployment_tags, expected['test']['deployment_tags']
        )
