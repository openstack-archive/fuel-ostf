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

import json
from mock import patch, MagicMock
import unittest2

from sqlalchemy.orm import sessionmaker

from fuel_plugin.ostf_adapter.wsgi import controllers
from fuel_plugin.ostf_adapter.storage import models, engine
from fuel_plugin.ostf_adapter.nose_plugin.nose_discovery import discovery


TEST_PATH = \
    'fuel_plugin/tests/functional/dummy_tests/deployment_types_tests'


class BaseTestController(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.Session = sessionmaker()
        cls.engine = engine.get_engine(
            dbpath='postgresql+psycopg2://ostf:ostf@localhost/ostf'
        )

    def setUp(self):
        #orm session wrapping
        connection = self.engine.connect()
        self.trans = connection.begin()

        self.Session.configure(bind=connection)
        self.session = self.Session()

        #test case level patching

        #mocking
        #request mocking
        self.request_mock = MagicMock()

        self.request_patcher = patch(
            'fuel_plugin.ostf_adapter.wsgi.controllers.request',
            self.request_mock
        )
        self.request_patcher.start()

        #pecan conf mocking
        self.pecan_conf_mock = MagicMock()
        self.pecan_conf_mock.nailgun.host = '127.0.0.1'
        self.pecan_conf_mock.nailgun.port = 8888

        #engine.get_session mocking
        self.request_mock.session = self.session

    def tearDown(self):
        #rollback changes to database
        #made by tests
        self.trans.rollback()
        self.session.close()

        #end of test_case patching
        self.request_patcher.stop()


class TestTestsController(BaseTestController):

    @classmethod
    def setUpClass(cls):
        super(TestTestsController, cls).setUpClass()

    def setUp(self):
        super(TestTestsController, self).setUp()
        self.controller = controllers.TestsController()

    def test_get(self):
        expected = {
            'cluster_id': 1,
            'frontend': [
                {
                    'status': None,
                    'taken': None,
                    'step': None,
                    'testset': 'ha_deployment_test',
                    'name': 'fake empty test',
                    'duration': None,
                    'message': None,
                    'id': ('fuel_plugin.tests.functional.dummy_tests.'
                           'deployment_types_tests.ha_deployment_test.'
                           'HATest.test_ha_depl'),
                    'description': (u'        This is empty test for any\n'
                                    '        ha deployment\n        '),
                },
                {
                    'status': None,
                    'taken': None,
                    'step': None,
                    'testset': 'ha_deployment_test',
                    'name': 'fake empty test',
                    'duration': '0sec',
                    'message': None,
                    'id': ('fuel_plugin.tests.functional.dummy_tests.'
                           'deployment_types_tests.ha_deployment_test.'
                           'HATest.test_ha_rhel_depl'),
                    'description': ('        This is fake tests for ha\n'
                                    '        rhel deployment\n        ')
                }
            ]
        }

        #patch CORE_PATH from nose_discovery in order
        #to process only testing data

        #haven't found more beautiful way to mock
        #discovery function in wsgi_utils
        def discovery_mock(**kwargs):
            kwargs['path'] = TEST_PATH
            return discovery(**kwargs)

        with patch(
            ('fuel_plugin.ostf_adapter.wsgi.wsgi_utils.'
             'nose_discovery.discovery'),
            discovery_mock
        ):
            with patch(
                'fuel_plugin.ostf_adapter.wsgi.wsgi_utils.conf',
                self.pecan_conf_mock
            ):
                res = self.controller.get(expected['cluster_id'])

        self.assertEqual(res, expected['frontend'])


class TestTestSetsController(BaseTestController):

    @classmethod
    def setUpClass(cls):
        super(TestTestSetsController, cls).setUpClass()

    def setUp(self):
        super(TestTestSetsController, self).setUp()
        self.controller = controllers.TestsetsController()

    def tearDown(self):
        super(TestTestSetsController, self).tearDown()

    def test_get(self):
        expected = {
            'cluster_id': 1,
            'frontend': [
                {
                    'id': 'ha_deployment_test',
                    'name': 'Fake tests for HA deployment'
                }
            ]
        }

        #patch CORE_PATH from nose_discovery in order
        #to process only testing data

        #haven't found more beautiful way to mock
        #discovery function in wsgi_utils
        def discovery_mock(**kwargs):
            kwargs['path'] = TEST_PATH
            return discovery(**kwargs)

        with patch(
            ('fuel_plugin.ostf_adapter.wsgi.wsgi_utils.'
             'nose_discovery.discovery'),
            discovery_mock
        ):
            with patch(
                'fuel_plugin.ostf_adapter.wsgi.wsgi_utils.conf',
                self.pecan_conf_mock
            ):
                res = self.controller.get(expected['cluster_id'])

        self.assertEqual(res, expected['frontend'])


class TestTestRunsController(BaseTestController):

    @classmethod
    def setUpClass(cls):
        super(TestTestRunsController, cls).setUpClass()

    def setUp(self):
        super(TestTestRunsController, self).setUp()

        #test_runs depends on tests and test_sets data
        #in database so we must execute discovery function
        #in setUp in order to provide this data
        depl_info = {
            'cluster_id': 1,
            'deployment_tags': set([
                'ha',
                'rhel'
            ])
        }

        discovery(
            session=self.session,
            deployment_info=depl_info,
            path=TEST_PATH
        )

        self.testruns = [
            {
                'testset': 'ha_deployment_test',
                'metadata': {'cluster_id': 1}
            }
        ]

        self.controller = controllers.TestrunsController()

    def tearDown(self):
        super(TestTestRunsController, self).tearDown()


class TestTestRunsPostController(TestTestRunsController):

    @classmethod
    def setUpClass(cls):
        super(TestTestRunsController, cls).setUpClass()

    def setUp(self):
        super(TestTestRunsPostController, self).setUp()

    def tearDown(self):
        super(TestTestRunsPostController, self).tearDown()

    def test_post(self):
        expected = {
            'testset': 'ha_deployment_test',
            'status': 'running',
            'cluster_id': 1,
            'tests': {
                'names': [
                    ('fuel_plugin.tests.functional.dummy_tests.'
                     'deployment_types_tests.ha_deployment_test.'
                     'HATest.test_ha_depl'),
                    ('fuel_plugin.tests.functional.dummy_tests.'
                     'deployment_types_tests.ha_deployment_test.'
                     'HATest.test_ha_rhel_depl')
                ]
            }
        }

        with patch(
            'fuel_plugin.ostf_adapter.wsgi.controllers.request.body',
            json.dumps(self.testruns)
        ):
            res = self.controller.post()[0]

        #checking wheter controller is working properly
        #by testing its blackbox behaviour
        for key in expected.keys():
            if key == 'tests':
                self.assertTrue(
                    set(expected[key]['names']) ==
                    set([test['id'] for test in res[key]])
                )
            else:
                self.assertTrue(expected[key] == res[key])

        #checking wheter all necessary writing to database
        #has been performed
        test_run = self.session.query(models.TestRun)\
            .filter_by(test_set_id=expected['testset'])\
            .filter_by(cluster_id=expected['cluster_id'])\
            .first()

        self.assertTrue(test_run)

        testrun_tests = self.session.query(models.Test)\
            .filter(models.Test.test_run_id != (None))\
            .all()

        tests_names = [
            test.name for test in testrun_tests
        ]
        self.assertTrue(set(tests_names) == set(expected['tests']['names']))

        self.assertTrue(
            all(
                [test.status == 'wait_running' for test in testrun_tests]
            )
        )


@unittest2.skip('Is broken, fixing is appreciated')
class TestTestRunsPutController(TestTestRunsController):

    @classmethod
    def setUpClass(cls):
        super(TestTestRunsPutController, cls).setUpClass()

    def setUp(self):
        super(TestTestRunsPutController, self).setUp()

        self.nose_adapter_session_patcher = patch(
            ('fuel_plugin.ostf_adapter.nose_plugin.'
             'nose_adapter.engine.get_session'),
            lambda *args: self.session
        )
        self.nose_adapter_session_patcher.start()

        #this test_case needs data on particular test_run
        #already present in database. That is suppotred by
        #following code

        with patch(
            'fuel_plugin.ostf_adapter.wsgi.controllers.request.body',
            json.dumps(self.testruns)
        ):
            self.stored_test_run = self.controller.post()[0]

    def tearDown(self):
        self.nose_adapter_session_patcher.stop()
        super(TestTestRunsPutController, self).tearDown()

    def test_put_stopped(self):
        expected = {
            'id': int(self.stored_test_run['id']),
            'testset': self.stored_test_run['testset'],
            'status': 'running',  # seems like incorrect !!!!!!!!!
            'cluster_id': 1,
            'tests': {
                'names': [
                    ('fuel_plugin.tests.functional.dummy_tests.'
                     'deployment_types_tests.ha_deployment_test.'
                     'HATest.test_ha_depl'),
                    ('fuel_plugin.tests.functional.dummy_tests.'
                     'deployment_types_tests.ha_deployment_test.'
                     'HATest.test_ha_rhel_depl')
                ]
            }
        }

        testruns_to_stop = [
            {
                'id': int(self.stored_test_run['id']),
                'metadata': {
                    'cluster_id': int(self.stored_test_run['cluster_id'])
                },
                'status': 'stopped'
            }
        ]

        with patch(
            'fuel_plugin.ostf_adapter.wsgi.controllers.request.body',
            json.dumps(testruns_to_stop)
        ):
            res = self.controller.put()[0]

        #checking wheter controller is working properly
        #by testing its blackbox behaviour
        for key in expected.keys():
            if key == 'tests':
                self.assertTrue(
                    set(expected[key]['names']) ==
                    set([test['id'] for test in res[key]])
                )
            else:
                self.assertTrue(expected[key] == res[key])

        testrun_tests = self.session.query(models.Test)\
            .filter(models.Test.test_run_id == expected['id'])\
            .all()

        tests_names = [
            test.name for test in testrun_tests
        ]
        self.assertTrue(set(tests_names) == set(expected['tests']['names']))

        self.assertTrue(
            all(
                [test.status == 'stopped' for test in testrun_tests]
            )
        )


class TestClusterRedployment(BaseTestController):

    @classmethod
    def setUpClass(cls):
        super(TestClusterRedployment, cls).setUpClass()

    def setUp(self):
        super(TestClusterRedployment, self).setUp()
        self.controller = controllers.TestsetsController()

    def tearDown(self):
        super(TestClusterRedployment, self).tearDown()

    def test_cluster_redeployment_with_different_tags(self):
        expected = {
            'cluster_id': 1,
            'old_test_set_id': 'ha_deployment_test',
            'new_test_set_id': 'multinode_deployment_test',
            'old_depl_tags': set(['ha', 'rhel', 'nova_network']),
            'new_depl_tags': set(['multinode', 'ubuntu', 'nova_network'])
        }

        def discovery_mock(**kwargs):
            kwargs['path'] = TEST_PATH
            return discovery(**kwargs)

        #start discoverying for testsets and tests for given cluster info
        with patch(
            ('fuel_plugin.ostf_adapter.wsgi.'
             'wsgi_utils.nose_discovery.discovery'),
            discovery_mock
        ):
            with patch(
                'fuel_plugin.ostf_adapter.wsgi.wsgi_utils.conf',
                self.pecan_conf_mock
            ):
                self.controller.get(expected['cluster_id'])

        cluster_state = self.session.query(models.ClusterState)\
            .filter_by(id=expected['cluster_id'])\
            .first()

        if not cluster_state:
            raise AssertionError(
                'There must be info about current cluster state in db'
            )

        self.assertEqual(
            set(cluster_state.deployment_tags),
            set(expected['old_depl_tags'])
        )

        test_set = self.session.query(models.TestSet)\
            .filter_by(id=expected['old_test_set_id'])\
            .filter_by(cluster_id=expected['cluster_id'])\
            .first()

        deployment_tags = test_set.deployment_tags \
            if test_set.deployment_tags else []

        self.assertTrue(
            set(deployment_tags).issubset(expected['old_depl_tags'])
        )

        #patch request_to_nailgun function in orded to emulate
        #redeployment of cluster
        cluster_data = set(
            ['multinode', 'ubuntu', 'nova_network']
        )

        with patch(
            ('fuel_plugin.ostf_adapter.wsgi.'
             'wsgi_utils._get_cluster_depl_tags'),
            lambda *args: cluster_data
        ):
            with patch(
                ('fuel_plugin.ostf_adapter.wsgi.'
                 'wsgi_utils.nose_discovery.discovery'),
                discovery_mock
            ):
                with patch(
                    'fuel_plugin.ostf_adapter.wsgi.wsgi_utils.conf',
                    self.pecan_conf_mock
                ):
                    self.controller.get(expected['cluster_id'])

        new_cluster_state = self.session.query(models.ClusterState)\
            .filter_by(id=expected['cluster_id'])\
            .first()

        self.assertEqual(
            set(new_cluster_state.deployment_tags),
            expected['new_depl_tags']
        )

        #check whether testset and bound with
        #it test have been deleted from db
        old_test_set = self.session.query(models.TestSet)\
            .filter_by(id=expected['old_test_set_id'])\
            .filter_by(cluster_id=expected['cluster_id'])\
            .first()

        if old_test_set:
            raise AssertionError(
                "There must not be test_set for old deployment in db"
            )

        old_tests = self.session.query(models.Test)\
            .filter_by(test_set_id=expected['old_test_set_id'])\
            .filter_by(cluster_id=expected['cluster_id'])\
            .all()

        if old_tests:
            raise AssertionError(
                "There must not be tests for old deployment in db"
            )

        #check whether new test set and tests are present in db
        #after 'redeployment' of cluster
        new_test_set = self.session.query(models.TestSet)\
            .filter_by(id=expected['new_test_set_id'])\
            .filter_by(cluster_id=expected['cluster_id'])\
            .first()
        self.assertTrue(new_test_set)
        deployment_tags = new_test_set.deployment_tags \
            if new_test_set.deployment_tags else []
        self.assertTrue(
            set(deployment_tags).issubset(expected['new_depl_tags'])
        )

        new_tests = self.session.query(models.Test)\
            .filter_by(test_set_id=expected['new_test_set_id'])\
            .filter_by(cluster_id=expected['cluster_id'])\
            .all()

        self.assertTrue(new_tests)
        for test in new_tests:
            deployment_tags = test.deployment_tags \
                if test.deployment_tags else []
            self.assertTrue(
                set(deployment_tags).issubset(expected['new_depl_tags'])
            )
