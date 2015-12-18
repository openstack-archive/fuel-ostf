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

import mock

from fuel_plugin.ostf_adapter.storage import models
from fuel_plugin.testing.tests import base


class TestTestsController(base.BaseWSGITest):

    def test_get(self):
        cluster_id = self.expected['cluster']['id']
        self.mock_api_for_cluster(cluster_id)
        resp = self.app.get(
            '/v1/tests/{0}'.format(cluster_id)
        )
        resp_tests = [test['id'] for test in resp.json]

        self.assertTrue(self.is_background_working)

        self.assertItemsEqual(
            resp_tests,
            self.expected['tests']
        )


class TestTestSetsController(base.BaseWSGITest):

    def test_get(self):
        self.expected['test_set_description'] = [
            'General fake tests',
            'Long running 25 secs fake tests',
            'Fake tests for HA deployment',
            'Test for presence of env variables inside of testrun subprocess'
        ]

        cluster_id = self.expected['cluster']['id']
        self.mock_api_for_cluster(cluster_id)

        resp = self.app.get(
            '/v1/testsets/{0}'.format(cluster_id)
        )
        resp_testsets_ids = [testset['id'] for testset in resp.json]

        self.assertTrue(self.is_background_working)

        self.assertItemsEqual(
            resp_testsets_ids,
            self.expected['test_sets']
        )

        self.assertItemsEqual(
            [testset['name'] for testset in resp.json],
            self.expected['test_set_description']
        )

        test_sets_order = (
            'general_test',
            'stopped_test',
            'ha_deployment_test',
            'environment_variables',
        )
        self.assertSequenceEqual(resp_testsets_ids, test_sets_order)


class TestTestRunsController(base.BaseWSGITest):

    def setUp(self):
        super(TestTestRunsController, self).setUp()
        self.plugin_mock = mock.Mock()
        self.plugin_mock.kill.return_value = True

        self.nose_plugin_patcher = mock.patch(
            'fuel_plugin.ostf_adapter.storage.models.nose_plugin.get_plugin',
            lambda *args: self.plugin_mock
        )
        self.nose_plugin_patcher.start()

        self.cluster_id = self.expected['cluster']['id']
        self.mock_api_for_cluster(self.cluster_id)

    def tearDown(self):
        super(TestTestRunsController, self).tearDown()
        self.nose_plugin_patcher.stop()

    def test_post(self):
        self.expected['testrun_post'] = {
            'testset': 'ha_deployment_test',
            'status': 'running',
            'cluster_id': 1,
            'tests': {
                'names': [
                    ('fuel_plugin.testing.fixture.dummy_tests.'
                     'deployment_types_tests.ha_deployment_test.'
                     'HATest.test_ha_depl'),
                    ('fuel_plugin.testing.fixture.dummy_tests.'
                     'deployment_types_tests.ha_deployment_test.'
                     'HATest.test_ha_rhel_depl')
                ]
            }
        }

        resp = self.app.post_json('/v1/testruns/', (
            {
                'testset': 'ha_deployment_test',
                'metadata': {'cluster_id': self.cluster_id}
            },
        ))

        resp_testrun = resp.json[0]

        for key in self.expected['testrun_post']:
            if key == 'tests':
                self.assertItemsEqual(
                    self.expected['testrun_post'][key]['names'],
                    [test['id'] for test in resp_testrun[key]]
                )
            else:
                self.assertEqual(
                    self.expected['testrun_post'][key],
                    resp_testrun[key]
                )

        self.session.query(models.TestRun)\
            .filter_by(test_set_id=self.expected['testrun_post']['testset'])\
            .filter_by(cluster_id=self.expected['testrun_post']['cluster_id'])\
            .one()

        testrun_tests = self.session.query(models.Test)\
            .filter(models.Test.test_run_id is not None)\
            .all()

        tests_names = [
            test.name for test in testrun_tests
        ]
        self.assertItemsEqual(
            tests_names,
            self.expected['testrun_post']['tests']['names']
        )

    def test_put_stopped(self):
        resp = self.app.post_json('/v1/testruns/', (
            {
                'testset': 'ha_deployment_test',
                'metadata': {'cluster_id': self.cluster_id}
            },
        ))
        resp_testrun = resp.json[0]

        self.session.query(models.Test)\
            .filter_by(test_run_id=resp_testrun['id'])\
            .update({'status': 'running'})

        # flush data which test is depend on into db
        self.session.commit()

        self.expected['testrun_put'] = {
            'id': resp_testrun['id'],
            'testset': 'ha_deployment_test',
            'cluster_id': 1,
            'tests': {
                'names': [
                    ('fuel_plugin.testing.fixture.dummy_tests.'
                     'deployment_types_tests.ha_deployment_test.'
                     'HATest.test_ha_depl'),
                    ('fuel_plugin.testing.fixture.dummy_tests.'
                     'deployment_types_tests.ha_deployment_test.'
                     'HATest.test_ha_rhel_depl')
                ]
            }
        }

        resp = self.app.put_json('/v1/testruns/', (
            {
                'status': 'stopped',
                'id': resp_testrun['id']
            },
        ))
        resp_testrun = resp.json[0]

        for key in self.expected['testrun_put'].keys():
            if key == 'tests':
                self.assertItemsEqual(
                    self.expected['testrun_put'][key]['names'],
                    [test['id'] for test in resp_testrun[key]]
                )
            else:
                self.assertEqual(
                    self.expected['testrun_put'][key], resp_testrun[key]
                )

        testrun_tests = self.session.query(models.Test)\
            .filter_by(test_run_id=self.expected['testrun_put']['id'])\
            .all()

        tests_names = [
            test.name for test in testrun_tests
        ]
        self.assertItemsEqual(
            tests_names,
            self.expected['testrun_put']['tests']['names']
        )

        self.assertTrue(
            all(
                [test.status == 'stopped' for test in testrun_tests]
            )
        )


class TestClusterRedeployment(base.BaseWSGITest):

    @mock.patch('fuel_plugin.ostf_adapter.mixins._get_cluster_attrs')
    def test_cluster_redeployment_with_different_tags(self,
                                                      m_get_cluster_attrs):
        m_get_cluster_attrs.return_value = {
            'deployment_tags': set(['multinode', 'centos']),
            'release_version': '2015.2-1.0'
        }

        cluster_id = self.expected['cluster']['id']
        self.app.get('/v1/testsets/{0}'.format(cluster_id))

        self.expected = {
            'cluster': {
                'id': 1,
                'deployment_tags': set(['multinode', 'ubuntu', 'nova_network'])
            },
            'test_sets': ['general_test',
                          'stopped_test', 'multinode_deployment_test',
                          'environment_variables'],
            'tests': [self.ext_id + test for test in [
                ('deployment_types_tests.multinode_deployment_test.'
                 'MultinodeTest.test_multi_novanet_depl'),
                ('deployment_types_tests.multinode_deployment_test.'
                 'MultinodeTest.test_multi_depl'),
                'general_test.DummyTest.test_fast_pass',
                'general_test.DummyTest.test_long_pass',
                'general_test.DummyTest.test_fast_fail',
                'general_test.DummyTest.test_fast_error',
                'general_test.DummyTest.test_fail_with_step',
                'general_test.DummyTest.test_skip',
                'general_test.DummyTest.test_skip_directly',
                'stopped_test.DummyTestsStopped.test_really_long',
                'stopped_test.DummyTestsStopped.test_one_no_so_long',
                'stopped_test.DummyTestsStopped.test_not_long_at_all',
                ('test_environment_variables.TestEnvVariables.'
                 'test_os_credentials_env_variables')
            ]]
        }

        # patch request_to_nailgun function in orded to emulate
        # redeployment of cluster
        m_get_cluster_attrs.return_value = {
            'deployment_tags': set(['multinode', 'ubuntu', 'nova_network']),
            'release_version': '2015.2-1.0'
        }

        self.app.get('/v1/testsets/{0}'.format(cluster_id))

        self.assertTrue(self.is_background_working)


class TestVersioning(base.BaseWSGITest):
    def test_discover_tests_with_versions(self):
        cluster_id = 6
        self.mock_api_for_cluster(cluster_id)
        self.app.get('/v1/testsets/{0}'.format(cluster_id))

        self.expected = {
            'cluster': {
                'id': 6,
                'deployment_tags': set(['releases_comparison'])
            },
            'test_sets': ['general_test', 'stopped_test', 'test_versioning',
                          'environment_variables'],
            'tests': [self.ext_id + test for test in [
                'general_test.DummyTest.test_fast_pass',
                'general_test.DummyTest.test_long_pass',
                'general_test.DummyTest.test_fast_fail',
                'general_test.DummyTest.test_fast_error',
                'general_test.DummyTest.test_fail_with_step',
                'general_test.DummyTest.test_skip',
                'general_test.DummyTest.test_skip_directly',
                'stopped_test.DummyTestsStopped.test_really_long',
                'stopped_test.DummyTestsStopped.test_one_no_so_long',
                'stopped_test.DummyTestsStopped.test_not_long_at_all',
                ('test_environment_variables.TestEnvVariables.'
                 'test_os_credentials_env_variables'),
                'test_versioning.TestVersioning.test_simple_fake_first',
            ]]
        }

        self.assertTrue(self.is_background_working)
