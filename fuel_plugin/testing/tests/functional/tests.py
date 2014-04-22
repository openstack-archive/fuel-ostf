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

import os
import time
from sqlalchemy import create_engine

from fuel_plugin.testing.tests.functional.base import \
    BaseAdapterTest, Response
from fuel_plugin.ostf_client.client import TestingAdapterClient as adapter


class AdapterTests(BaseAdapterTest):

    @classmethod
    def setUpClass(cls):

        url = 'http://0.0.0.0:8777/v1'

        cls.mapping = {
            ('fuel_plugin.testing.fixture.dummy_tests.'
             'general_test.Dummy_test.test_fast_pass'): 'fast_pass',
            ('fuel_plugin.testing.fixture.dummy_tests.'
             'general_test.Dummy_test.test_fast_error'): 'fast_error',
            ('fuel_plugin.testing.fixture.dummy_tests.'
             'general_test.Dummy_test.test_fast_fail'): 'fast_fail',
            ('fuel_plugin.testing.fixture.dummy_tests.'
             'general_test.Dummy_test.test_long_pass'): 'long_pass',
            ('fuel_plugin.testing.fixture.dummy_tests.'
             'general_test.Dummy_test.test_fail_with_step'): 'fail_step',
            ('fuel_plugin.testing.fixture.dummy_tests.'
             'general_test.Dummy_test.test_skip'): 'skip',
            ('fuel_plugin.testing.fixture.dummy_tests.'
             'general_test.Dummy_test.test_skip_directly'): 'skip_directly',
            ('fuel_plugin.testing.fixture.dummy_tests.stopped_test.'
             'dummy_tests_stopped.test_really_long'): 'really_long',
            ('fuel_plugin.testing.fixture.dummy_tests.stopped_test.'
             'dummy_tests_stopped.test_not_long_at_all'): 'not_long',
            ('fuel_plugin.testing.fixture.dummy_tests.stopped_test.'
             'dummy_tests_stopped.test_one_no_so_long'): 'so_long',
            ('fuel_plugin.testing.fixture.dummy_tests.deployment_types_tests.'
             'ha_deployment_test.HATest.test_ha_depl'): 'ha_depl',
            ('fuel_plugin.testing.fixture.dummy_tests.deployment_types_tests.'
             'ha_deployment_test.HATest.test_ha_rhel_depl'): 'ha_rhel_depl'
        }
        cls.testsets = {
            "ha_deployment_test": [],
            "general_test": [
                'fast_pass',
                'fast_error',
                'fast_fail',
                'long_pass',
                'skip',
                'skip_directly'
            ],
            "stopped_test": [
                'really_long',
                'not_long',
                'so_long'
            ]
        }

        cls.adapter = adapter(url)
        cls.client = cls.init_client(url)

    @classmethod
    def tearDownClass(cls):
        lock_path = '/tmp/ostf_locks'
        if os.path.exists(lock_path):
            for f in os.listdir(lock_path):
                f_path = os.path.join(lock_path, f)
                if os.path.isfile(f_path):
                    os.remove(f_path)

    def tearDown(self):
        eng = create_engine(
            'postgresql+psycopg2://ostf:ostf@localhost/ostf'
        )

        eng.execute('delete from cluster_testing_pattern;')
        eng.execute('delete from cluster_state;')

    def test_list_testsets(self):
        """Verify that self.testsets are in json response
        """
        cluster_id = 1

        json = self.adapter.testsets(cluster_id).json()
        response_testsets = [item['id'] for item in json]
        for testset in self.testsets:
            msg = '"{test}" not in "{response}"'.format(
                test=testset,
                response=response_testsets
            )
            self.assertTrue(testset in response_testsets, msg)

    def test_list_tests(self):
        """Verify that self.tests are in json response
        """
        cluster_id = 1
        json = self.adapter.tests(cluster_id).json()
        response_tests = [item['id'] for item in json]
        for test in self.mapping.keys():
            msg = '"{test}" not in "{response}"'.format(
                test=test.capitalize(),
                response=response_tests
            )
            self.assertTrue(test in response_tests, msg)

    def test_run_testset(self, use_objects=False):
        """Verify that test status changes in time from running to success
        """
        testsets = ["general_test", "stopped_test"]
        cluster_id = 1

        # make sure we have data about test_sets in db
        self.adapter.testsets(cluster_id)
        for testset in testsets:
            self.client.start_testrun(testset, cluster_id, use_objects)

        time.sleep(5)

        resp = self.client.testruns_last(cluster_id)

        assertions = Response(
            [
                {
                    'testset': 'general_test',
                    'status': 'running',
                    'tests': [],
                    'meta': None,
                    'cluster_id': 1,
                },
                {
                    'testset': 'stopped_test',
                    'status': 'running',
                    'tests': [],
                    'meta': None,
                    'cluster_id': 1,
                }
            ]
        )

        self.compare(resp, assertions)
        time.sleep(30)

        resp = self.client.testruns_last(cluster_id)

        assertions.general_test['status'] = 'finished'
        assertions.stopped_test['status'] = 'finished'

        self.compare(resp, assertions)

    def test_stop_testset(self, use_objects=False):
        """Verify that long running testrun can be stopped
        """
        testset = "stopped_test"
        cluster_id = 1

        # make sure we have all needed data in db
        # for this test case
        self.adapter.testsets(cluster_id)

        self.client.start_testrun(testset, cluster_id, use_objects)
        time.sleep(20)

        resp = self.client.testruns_last(cluster_id)

        assertions = Response([
            {
                'testset': 'stopped_test',
                'status': 'running',
                'tests': [],
                'meta': None,
                'cluster_id': 1
            }
        ])

        self.compare(resp, assertions)

        self.client.stop_testrun_last(testset, cluster_id, use_objects)
        time.sleep(5)
        resp = self.client.testruns_last(cluster_id)

        assertions.stopped_test['status'] = 'finished'
        self.compare(resp, assertions)

    def test_cant_start_while_running(self, use_objects=False):
        """Verify that you can't start new testrun
        for the same cluster_id while previous run
        is running
        """
        testsets = [
            "stopped_test",
            "general_test"
        ]
        cluster_id = 1

        self.adapter.testsets(cluster_id)

        for testset in testsets:
            self.client.start_testrun(testset, cluster_id, use_objects)
        self.client.testruns_last(cluster_id)

        for testset in testsets:
            resp = self.client.start_testrun(testset, cluster_id, use_objects)

            msg = (
                "Response {0} is not empty when you try to start testrun"
                " with testset and cluster_id that are already running"
            ).format(resp)

            self.assertTrue(resp.is_empty, msg)

    def test_start_many_runs(self):
        """Verify that you can start more than one
        testruns in a row with different cluster_id
        """
        testset = "general_test"
        cluster_id = 1

        self.adapter.testsets(cluster_id)

        for cluster_id in range(1, 2):
            resp = self.client.start_testrun(testset, cluster_id)
            msg = '{0} was empty'.format(resp.request)
            self.assertFalse(resp.is_empty, msg)

        '''TODO: Rewrite assertions to verity that all
        5 testruns ended with appropriate status
        '''

    def test_run_single_test(self, use_objects=False):
        """Verify that you can run individual tests from given testset"""
        testset = "general_test"
        tests = [
            ('fuel_plugin.testing.fixture.dummy_tests.'
             'general_test.Dummy_test.test_fast_pass'),
            ('fuel_plugin.testing.fixture.dummy_tests.'
             'general_test.Dummy_test.test_fast_error')
        ]
        cluster_id = 1

        # make sure that we have all needed data in db
        self.adapter.testsets(cluster_id)

        resp = self.client.start_testrun_tests(testset, tests, cluster_id,
                                               use_objects)

        assertions = Response([
            {
                'testset': 'general_test',
                'status': 'running',
                'tests': [
                    {
                        'status': 'disabled',
                        'name': 'Fast fail with step',
                        'id': ('fuel_plugin.testing.fixture.dummy_tests.'
                               'general_test.Dummy_test.test_fail_with_step'),
                    },
                    {
                        'status': 'wait_running',
                        'name': 'And fast error',
                        'id': ('fuel_plugin.testing.fixture.dummy_tests.'
                               'general_test.Dummy_test.test_fast_error'),
                    },
                    {
                        'status': 'disabled',
                        'name': 'Fast fail',
                        'id': ('fuel_plugin.testing.fixture.dummy_tests.'
                               'general_test.Dummy_test.test_fast_fail'),
                    },
                    {
                        'status': 'wait_running',
                        'name': 'fast pass test',
                        'id': ('fuel_plugin.testing.fixture.dummy_tests.'
                               'general_test.Dummy_test.test_fast_pass'),
                    },
                    {
                        'status': 'disabled',
                        'name': 'Will sleep 5 sec',
                        'id': ('fuel_plugin.testing.fixture.dummy_tests.'
                               'general_test.Dummy_test.test_long_pass'),
                    },
                    {
                        'status': 'disabled',
                        'name': 'Skip',
                        'id': ('fuel_plugin.testing.fixture.dummy_tests.'
                               'general_test.Dummy_test.test_skip'),
                    },
                    {
                        'status': 'disabled',
                        'name': 'Skip with exception',
                        'id': ('fuel_plugin.testing.fixture.dummy_tests.'
                               'general_test.Dummy_test.test_skip_directly'),
                    }
                ],
                'cluster_id': 1,
            }
        ])

        self.compare(resp, assertions)

        time.sleep(3)

        resp = self.client.testruns_last(cluster_id)

        assertions.general_test['status'] = 'finished'
        for test in assertions.general_test['tests']:
            if test['name'] == 'And fast error':
                test['status'] = 'error'
            elif test['name'] == 'fast pass test':
                test['status'] = 'success'

        self.compare(resp, assertions)

    def test_single_test_restart(self):
        """Verify that you restart individual tests for given testrun"""
        testset = "general_test"
        tests = [
            ('fuel_plugin.testing.fixture.dummy_tests.'
             'general_test.Dummy_test.test_fast_pass'),
            ('fuel_plugin.testing.fixture.dummy_tests.general_test.'
             'Dummy_test.test_fast_fail')
        ]
        cluster_id = 1

        # make sure we have all needed data in db
        self.adapter.testsets(cluster_id)

        self.client.run_testset_with_timeout(testset, cluster_id, 10)

        resp = self.client.restart_tests_last(testset, tests, cluster_id)

        assertions = Response([
            {
                'testset': 'general_test',
                'status': 'running',
                'tests': [
                    {
                        'status': 'failure',
                        'name': 'Fast fail with step',
                        'id': ('fuel_plugin.testing.fixture.dummy_tests.'
                               'general_test.Dummy_test.test_fail_with_step'),
                    },
                    {
                        'status': 'error',
                        'name': 'And fast error',
                        'id': ('fuel_plugin.testing.fixture.dummy_tests.'
                               'general_test.Dummy_test.test_fast_error'),
                    },
                    {
                        'status': 'wait_running',
                        'name': 'Fast fail',
                        'id': ('fuel_plugin.testing.fixture.dummy_tests.'
                               'general_test.Dummy_test.test_fast_fail'),
                    },
                    {
                        'status': 'wait_running',
                        'name': 'fast pass test',
                        'id': ('fuel_plugin.testing.fixture.dummy_tests.'
                               'general_test.Dummy_test.test_fast_pass'),
                    },
                    {
                        'status': 'success',
                        'name': 'Will sleep 5 sec',
                        'id': ('fuel_plugin.testing.fixture.dummy_tests.'
                               'general_test.Dummy_test.test_long_pass'),
                    },
                    {
                        'status': 'skipped',
                        'name': 'Skip',
                        'id': ('fuel_plugin.testing.fixture.dummy_tests.'
                               'general_test.Dummy_test.test_skip'),
                    },
                    {
                        'status': 'skipped',
                        'name': 'Skip with exception',
                        'id': ('fuel_plugin.testing.fixture.dummy_tests.'
                               'general_test.Dummy_test.test_skip_directly'),
                    }
                ],
                'cluster_id': 1,
            }
        ])

        self.compare(resp, assertions)
        time.sleep(10)

        resp = self.client.testruns_last(cluster_id)

        assertions.general_test['status'] = 'finished'
        for test in assertions.general_test['tests']:
            if test['name'] == 'Fast fail':
                test['status'] = 'failure'
            elif test['name'] == 'fast pass test':
                test['status'] = 'success'

        self.compare(resp, assertions)

    def test_restart_combinations(self):
        """Verify that you can restart both tests that
        ran and did not run during single test start"""
        testset = "general_test"
        tests = [
            ('fuel_plugin.testing.fixture.dummy_tests.'
             'general_test.Dummy_test.test_fast_pass'),
            ('fuel_plugin.testing.fixture.dummy_tests.'
             'general_test.Dummy_test.test_fast_fail')
        ]
        disabled_test = [
            ('fuel_plugin.testing.fixture.dummy_tests.'
             'general_test.Dummy_test.test_fast_error')
        ]
        cluster_id = 1

        # make sure we have all needed data in db
        self.adapter.testsets(cluster_id)

        self.client.run_with_timeout(testset, tests, cluster_id, 70)
        self.client.restart_with_timeout(testset, tests, cluster_id, 10)

        resp = self.client.restart_tests_last(testset, disabled_test,
                                              cluster_id)

        assertions = Response([
            {
                'testset': 'general_test',
                'status': 'running',
                'tests': [
                    {
                        'status': 'disabled',
                        'name': 'Fast fail with step',
                        'id': ('fuel_plugin.testing.fixture.dummy_tests.'
                               'general_test.Dummy_test.test_fail_with_step'),
                    },
                    {
                        'status': 'wait_running',
                        'name': 'And fast error',
                        'id': ('fuel_plugin.testing.fixture.dummy_tests.'
                               'general_test.Dummy_test.test_fast_error'),
                    },
                    {
                        'status': 'failure',
                        'name': 'Fast fail',
                        'id': ('fuel_plugin.testing.fixture.dummy_tests.'
                               'general_test.Dummy_test.test_fast_fail'),
                    },
                    {
                        'status': 'success',
                        'name': 'fast pass test',
                        'id': ('fuel_plugin.testing.fixture.dummy_tests.'
                               'general_test.Dummy_test.test_fast_pass'),
                    },
                    {
                        'status': 'disabled',
                        'name': 'Will sleep 5 sec',
                        'id': ('fuel_plugin.testing.fixture.dummy_tests.'
                               'general_test.Dummy_test.test_long_pass'),
                    },
                    {
                        'status': 'disabled',
                        'name': 'Skip',
                        'id': ('fuel_plugin.testing.fixture.dummy_tests.'
                               'general_test.Dummy_test.test_skip'),
                    },
                    {
                        'status': 'disabled',
                        'name': 'Skip with exception',
                        'id': ('fuel_plugin.testing.fixture.dummy_tests.'
                               'general_test.Dummy_test.test_skip_directly'),
                    }
                ],
                'cluster_id': 1,
            }
        ])
        self.compare(resp, assertions)
        time.sleep(5)

        resp = self.client.testruns_last(cluster_id)

        assertions.general_test['status'] = 'finished'
        for test in assertions.general_test['tests']:
            if test['name'] == 'And fast error':
                test['status'] = 'error'
        self.compare(resp, assertions)

    def test_cant_restart_during_run(self):
        testset = 'general_test'
        tests = [
            ('fuel_plugin.testing.fixture.dummy_tests.'
             'general_test.Dummy_test.test_fast_pass'),
            ('fuel_plugin.testing.fixture.dummy_tests.'
             'general_test.Dummy_test.test_fast_fail'),
            ('fuel_plugin.testing.fixture.dummy_tests.'
             'general_test.Dummy_test.test_fast_pass')
        ]
        cluster_id = 1

        # make sure that we have all needen data in db
        self.adapter.testsets(cluster_id)

        self.client.start_testrun(testset, cluster_id)
        time.sleep(2)

        resp = self.client.restart_tests_last(testset, tests, cluster_id)
        msg = ('Response was not empty after trying'
               ' to restart running testset:\n {0}').format(resp.request)
        self.assertTrue(resp.is_empty, msg)

    def test_nose_adapter_error_while_running_tests(self):
        testset = 'test_with_error'
        cluster_id = 4

        # make sure we have all needed data in db
        self.adapter.testsets(cluster_id)

        self.client.start_testrun(testset, cluster_id)
        time.sleep(5)

        resp = self.client.testruns_last(cluster_id)

        assertions = Response([
            {
                'testset': 'test_with_error',
                'status': 'finished',
                'cluster_id': 4,
                'tests': [
                    {
                        'id': (
                            'fuel_plugin.testing.fixture.'
                            'dummy_tests.test_with_error.WithErrorTest.'
                            'test_supposed_to_be_fail'
                        ),
                        'status': 'error'
                    },
                    {
                        'id': (
                            'fuel_plugin.testing.fixture.'
                            'dummy_tests.test_with_error.WithErrorTest.'
                            'test_supposed_to_be_success'
                        ),
                        'status': 'error'
                    }
                ]

            }
        ])

        self.compare(resp, assertions)

    def test_dependent_testsets(self):
        testsets = ['gemini_first', 'gemini_second']
        cluster_id = 5

        # make sure we have all needed data in db
        self.adapter.testsets(cluster_id)

        self.client.start_multiple_testruns(testsets, cluster_id)
        time.sleep(5)

        resp = self.client.testruns()

        assertions = Response([
            {
                'testset': 'gemini_first',
                'status': 'running',
                'tests': [
                    {
                        'id': (
                            'fuel_plugin.testing.fixture.'
                            'dummy_tests.dependent_testsets.'
                            'gemini_first_test.TestGeminiFirst.'
                            'test_fake_long_succes_gf'
                        ),
                        'status': 'running'
                    },
                    {
                        'id': (
                            'fuel_plugin.testing.fixture.'
                            'dummy_tests.dependent_testsets.'
                            'gemini_first_test.TestGeminiFirst.'
                            'test_fake_quick_success_gf'
                        ),
                        'status': 'wait_running'
                    }
                ]
            },
            {
                'testset': 'gemini_second',
                'status': 'running',
                'tests': [
                    {
                        'id': (
                            'fuel_plugin.testing.fixture.'
                            'dummy_tests.dependent_testsets.'
                            'gemini_second_test.TestGeminiSecond.'
                            'test_fake_long_succes_gs'
                        ),
                        'status': 'wait_running'
                    },
                    {
                        'id': (
                            'fuel_plugin.testing.fixture.'
                            'dummy_tests.dependent_testsets.'
                            'gemini_second_test.TestGeminiSecond.'
                            'test_fake_quick_success_gs'
                        ),
                        'status': 'wait_running'
                    }
                ]
            }
        ])

        self.compare(resp, assertions)

    def test_use_objects_data_format(self):
        self.test_run_testset(use_objects=True)
        self.test_run_single_test(use_objects=True)
        self.test_stop_testset(use_objects=True)
