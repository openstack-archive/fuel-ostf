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
from sqlalchemy.orm import sessionmaker

from fuel_plugin.ostf_adapter.nose_plugin import nose_discovery
from fuel_plugin.ostf_adapter.storage import models
from fuel_plugin.ostf_adapter.storage import engine


class BaseTestNoseDiscovery(unittest2.TestCase):
    '''
    All test writing to database is wrapped in
    non-ORM transaction which is created in
    test_case setUp method and rollbacked in
    tearDown, so that keep prodaction base clean
    '''

    @classmethod
    def setUpClass(cls):
        cls._mocked_pecan_conf = Mock()
        cls._mocked_pecan_conf.dbpath = \
            'postgresql+psycopg2://ostf:ostf@localhost/ostf'

        cls.Session = sessionmaker()

        with patch(
            'fuel_plugin.ostf_adapter.storage.engine.conf',
            cls._mocked_pecan_conf
        ):
            cls.engine = engine.get_engine()

    def setUp(self):
        #database transaction wrapping
        connection = self.engine.connect()
        self.trans = connection.begin()

        self.Session.configure(bind=connection)
        self.session = self.Session(bind=connection)

        #test_case level patching
        self.mocked_get_session = lambda *args: self.session

        self.session_patcher = patch(
            'fuel_plugin.ostf_adapter.nose_plugin.nose_discovery.engine.get_session',
            self.mocked_get_session
        )
        self.session_patcher.start()

        self.fixtures = {
            'ha_deployment_test': {
                'cluster_id': 1,
                'deployment_tags': set([
                    'ha',
                    'rhel'
                ])
            },
            'multinode_deployment_test': {
                'cluster_id': 2,
                'deployment_tags': set([
                    'multinode',
                    'ubuntu'
                ])
            }
        }

    def tearDown(self):
        #end patching
        self.session_patcher.stop()

        #unwrapping
        self.trans.rollback()
        self.session.close()


class TestNoseDiscovery(BaseTestNoseDiscovery):

    @classmethod
    def setUpClass(cls):
        super(TestNoseDiscovery, cls).setUpClass()

    def setUp(self):
        super(TestNoseDiscovery, self).setUp()

    def tearDown(self):
        super(TestNoseDiscovery, self).tearDown()

    def test_discovery_testsets(self):
        expected = {
            'id': 'ha_deployment_test',
            'cluster_id': 1,
            'deployment_tags': ['ha']
        }

        nose_discovery.discovery(
            path='fuel_plugin.tests.functional.dummy_tests.deployment_types_tests.ha_deployment_test',
            deployment_info=self.fixtures['ha_deployment_test']
        )

        test_set = self.session.query(models.TestSet)\
            .filter_by(id=expected['id'])\
            .filter_by(cluster_id=expected['cluster_id'])\
            .one()

        self.assertEqual(
            test_set.deployment_tags,
            expected['deployment_tags']
        )

    def test_discovery_tests(self):
        expected = {
            'test_set_id': 'ha_deployment_test',
            'cluster_id': 1,
            'results_count': 2,
            'results_data': {
                'names': [
                    'fuel_plugin.tests.functional.dummy_tests.deployment_types_tests.ha_deployment_test.HATest.test_ha_rhel_depl',
                    'fuel_plugin.tests.functional.dummy_tests.deployment_types_tests.ha_deployment_test.HATest.test_ha_depl'
                ]
            }
        }
        nose_discovery.discovery(
            path='fuel_plugin.tests.functional.dummy_tests.deployment_types_tests.ha_deployment_test',
            deployment_info=self.fixtures['ha_deployment_test']
        )

        tests = self.session.query(models.Test)\
            .filter_by(test_set_id=expected['test_set_id'])\
            .filter_by(cluster_id=expected['cluster_id'])\
            .all()

        self.assertTrue(len(tests) == expected['results_count'])

        for test in tests:
            self.assertTrue(test.name in expected['results_data']['names'])
            self.assertTrue(
                set(test.deployment_tags)
                .issubset(self.fixtures['ha_deployment_test']['deployment_tags'])
            )

    def test_get_proper_description(self):
        expected = {
            'title': 'fake empty test',
            'name': ('fuel_plugin.tests.functional.'
                     'dummy_tests.deployment_types_tests.'
                     'ha_deployment_test.HATest.test_ha_rhel_depl'),
            'duration': '0sec',
            'test_set_id': 'ha_deployment_test',
            'cluster_id': self.fixtures['ha_deployment_test']['cluster_id'],
            'deployment_tags': ['ha', 'rhel']

        }

        nose_discovery.discovery(
            path='fuel_plugin.tests.functional.dummy_tests.deployment_types_tests.ha_deployment_test',
            deployment_info=self.fixtures['ha_deployment_test']
        )

        test = self.session.query(models.Test)\
            .filter_by(name=expected['name'])\
            .filter_by(cluster_id=expected['cluster_id'])\
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
