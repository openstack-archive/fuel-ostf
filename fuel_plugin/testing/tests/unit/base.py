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
from mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fuel_plugin.ostf_adapter.nose_plugin.nose_discovery import discovery
from fuel_plugin.ostf_adapter.storage import models
from fuel_plugin.ostf_adapter import mixins

TEST_PATH = 'fuel_plugin/testing/fixture/dummy_tests'


class BaseWSGITest(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dbpath = 'postgresql+psycopg2://ostf:ostf@localhost/ostf'
        cls.Session = sessionmaker()
        cls.engine = create_engine(cls.dbpath)

        cls.ext_id = 'fuel_plugin.testing.fixture.dummy_tests.'
        cls.expected = {
            'cluster': {
                'id': 1,
                'deployment_tags': set(['ha', 'rhel', 'nova_network'])
            },
            'test_sets': ['general_test',
                          'stopped_test', 'ha_deployment_test'],
            'tests': [cls.ext_id + test for test in [
                ('deployment_types_tests.ha_deployment_test.'
                 'HATest.test_ha_depl'),
                ('deployment_types_tests.ha_deployment_test.'
                 'HATest.test_ha_rhel_depl'),
                'general_test.Dummy_test.test_fast_pass',
                'general_test.Dummy_test.test_long_pass',
                'general_test.Dummy_test.test_fast_fail',
                'general_test.Dummy_test.test_fast_error',
                'general_test.Dummy_test.test_fail_with_step',
                'general_test.Dummy_test.test_skip',
                'general_test.Dummy_test.test_skip_directly',
                'stopped_test.dummy_tests_stopped.test_really_long',
                'stopped_test.dummy_tests_stopped.test_one_no_so_long',
                'stopped_test.dummy_tests_stopped.test_not_long_at_all'
            ]]
        }

    def setUp(self):
        # orm session wrapping
        self.connection = self.engine.connect()
        self.trans = self.connection.begin()

        self.Session.configure(
            bind=self.connection
        )
        self.session = self.Session()

        test_sets = self.session.query(models.TestSet).all()

        # need this if start unit tests in conjuction with integration
        if not test_sets:
            discovery(path=TEST_PATH, session=self.session)

        mixins.cache_test_repository(self.session)

        # mocking
        # request mocking
        self.request_mock = MagicMock()

        self.request_patcher = patch(
            'fuel_plugin.ostf_adapter.wsgi.controllers.request',
            self.request_mock
        )
        self.request_patcher.start()

        # pecan conf mocking
        self.pecan_conf_mock = MagicMock()
        self.pecan_conf_mock.nailgun.host = '127.0.0.1'
        self.pecan_conf_mock.nailgun.port = 8888

        self.pecan_conf_patcher = patch(
            'fuel_plugin.ostf_adapter.mixins.conf',
            self.pecan_conf_mock
        )
        self.pecan_conf_patcher.start()

        # pecan conf mocking in wsgi.controllers
        self.wsgi_controllers_pecan_conf_mock = MagicMock()
        self.controllers_pecan_conf_patcher = patch(
            'fuel_plugin.ostf_adapter.wsgi.controllers.conf',
            self.wsgi_controllers_pecan_conf_mock
        )
        self.controllers_pecan_conf_patcher.start()

        # engine.get_session mocking
        self.request_mock.session = self.session

    def tearDown(self):
        # rollback changes to database
        # made by tests
        self.trans.rollback()
        self.session.close()
        self.connection.close()

        # end of test_case patching
        self.request_patcher.stop()
        self.pecan_conf_patcher.stop()
        self.controllers_pecan_conf_patcher.stop()

        mixins.TEST_REPOSITORY = []

    @property
    def is_background_working(self):
        is_working = True

        cluster_state = self.session.query(models.ClusterState)\
            .filter_by(id=self.expected['cluster']['id'])\
            .one()
        is_working = is_working and set(cluster_state.deployment_tags) == \
            self.expected['cluster']['deployment_tags']

        cluster_testing_patterns = self.session\
            .query(models.ClusterTestingPattern)\
            .filter_by(cluster_id=self.expected['cluster']['id'])\
            .all()

        for testing_pattern in cluster_testing_patterns:
            is_working = is_working and \
                (testing_pattern.test_set_id in self.expected['test_sets'])

            is_working = is_working and set(testing_pattern.tests)\
                .issubset(set(self.expected['tests']))

        return is_working
