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
from mock import patch, Mock

from fuel_plugin.ostf_adapter.wsgi import controllers
from fuel_plugin.ostf_adapter.storage import models

from fuel_plugin.testing.tests.unit import base


class TestTestsController(base.BaseWSGITest):

    def setUp(self):
        super(TestTestsController, self).setUp()
        self.controller = controllers.TestsController()

    def test_get(self):
        res = self.controller.get(self.expected['cluster']['id'])

        self.assertTrue(self.is_background_working)

        self.assertTrue(len(res) == len(self.expected['tests']))
        self.assertTrue(
            sorted([test['id'] for test in res]),
            sorted(self.expected['tests'])
        )


class TestTestSetsController(base.BaseWSGITest):

    def setUp(self):
        super(TestTestSetsController, self).setUp()
        self.controller = controllers.TestsetsController()

    def test_get(self):
        self.expected['test_set_description'] = [
            'General fake tests',
            'Long running 25 secs fake tests',
            'Fake tests for HA deployment'
        ]
        res = self.controller.get(self.expected['cluster']['id'])

        self.assertTrue(self.is_background_working)

        self.assertTrue(
            sorted([testset['id'] for testset in res]) ==
            sorted(self.expected['test_sets'])
        )
        self.assertTrue(
            sorted([testset['name'] for testset in res]) ==
            sorted(self.expected['test_set_description'])
        )

        test_set_order = {
            'general_test': 0,
            'stopped_test': 1,
            'ha_deployment_test': 2
        }

        resp_elements = [testset['id'] for testset in res]
        for test_set in resp_elements:
            self.assertTrue(
                test_set_order[test_set] == resp_elements.index(test_set)
            )


class TestTestRunsController(base.BaseWSGITest):

    def setUp(self):
        super(TestTestRunsController, self).setUp()

        controllers.TestsetsController().get(self.expected['cluster']['id'])

        self.request_mock.body = json.dumps([
            {
                'testset': 'ha_deployment_test',
                'metadata': {'cluster_id': 1}
            }]
        )

        self.controller = controllers.TestrunsController()

        self.plugin_mock = Mock()
        self.plugin_mock.kill.return_value = True

        self.nose_plugin_patcher = patch(
            'fuel_plugin.ostf_adapter.storage.models.nose_plugin.get_plugin',
            lambda *args: self.plugin_mock
        )
        self.nose_plugin_patcher.start()

    def tearDown(self):
        super(TestTestRunsController, self).tearDown()

        self.nose_plugin_patcher.stop()


class TestTestRunsPostController(TestTestRunsController):

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

        res = self.controller.post()[0]

        for key in self.expected['testrun_post'].keys():
            if key == 'tests':
                self.assertTrue(
                    sorted(self.expected['testrun_post'][key]['names']) ==
                    sorted([test['id'] for test in res[key]])
                )
            else:
                self.assertTrue(
                    self.expected['testrun_post'][key] == res[key]
                )

        test_run = self.session.query(models.TestRun)\
            .filter_by(test_set_id=self.expected['testrun_post']['testset'])\
            .filter_by(cluster_id=self.expected['testrun_post']['cluster_id'])\
            .one()

        testrun_tests = self.session.query(models.Test)\
            .filter(models.Test.test_run_id != (None))\
            .all()

        tests_names = [
            test.name for test in testrun_tests
        ]
        self.assertTrue(
            sorted(tests_names) ==
            sorted(self.expected['testrun_post']['tests']['names'])
        )


class TestTestRunsPutController(TestTestRunsController):

    def setUp(self):
        super(TestTestRunsPutController, self).setUp()
        self.test_run = self.controller.post()[0]

        with self.session.begin(subtransactions=True):
            self.session.query(models.Test)\
                .filter_by(test_run_id=int(self.test_run['id']))\
                .update({'status': 'running'})

        self.request_mock.body = json.dumps(
            [{
                'status': 'stopped',
                'id': self.test_run['id']
            }]
        )

    def test_put_stopped(self):
        self.expected['testrun_put'] = {
            'id': int(self.test_run['id']),
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

        res = self.controller.put()[0]

        for key in self.expected['testrun_put'].keys():
            if key == 'tests':
                self.assertTrue(
                    sorted(self.expected['testrun_put'][key]['names']) ==
                    sorted([test['id'] for test in res[key]])
                )
            else:
                self.assertTrue(
                    self.expected['testrun_put'][key] == res[key]
                )

        testrun_tests = self.session.query(models.Test)\
            .filter_by(test_run_id=self.expected['testrun_put']['id'])\
            .all()

        tests_names = [
            test.name for test in testrun_tests
        ]
        self.assertTrue(
            sorted(tests_names) ==
            sorted(self.expected['testrun_put']['tests']['names'])
        )

        self.assertTrue(
            all(
                [test.status == 'stopped' for test in testrun_tests]
            )
        )


class TestClusterRedeployment(base.BaseWSGITest):

    def setUp(self):
        super(TestClusterRedeployment, self).setUp()
        self.controller = controllers.TestsetsController()
        self.controller.get(self.expected['cluster']['id'])

    def test_cluster_redeployment_with_different_tags(self):
        self.expected = {
            'cluster': {
                'id': 1,
                'deployment_tags': set(['multinode', 'ubuntu', 'nova_network'])
            },
            'test_sets': ['general_test',
                          'stopped_test', 'multinode_deployment_test'],
            'tests': [self.ext_id + test for test in [
                ('deployment_types_tests.multinode_deployment_test.'
                 'MultinodeTest.test_multi_novanet_depl'),
                ('deployment_types_tests.multinode_deployment_test.'
                 'MultinodeTest.test_multi_depl'),
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

        #patch request_to_nailgun function in orded to emulate
        #redeployment of cluster
        cluster_data = set(
            ['multinode', 'ubuntu', 'nova_network']
        )

        with patch(
            ('fuel_plugin.ostf_adapter.mixins._get_cluster_depl_tags'),
            lambda *args: cluster_data
        ):
            self.controller.get(self.expected['cluster']['id'])

        self.assertTrue(self.is_background_working)
