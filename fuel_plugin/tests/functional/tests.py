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

import time
import mock

from fuel_plugin.tests.functional.base import BaseAdapterTest, Response
from fuel_plugin.ostf_client.client import TestingAdapterClient as adapter

from fuel_plugin.ostf_adapter.storage import engine, models


class AdapterTests(BaseAdapterTest):

    @classmethod
    def setUpClass(cls):

        url = 'http://0.0.0.0:8989/v1'

        cls.mapping = {
            'fuel_plugin.tests.functional.dummy_tests.general_test.Dummy_test.test_fast_pass':  'fast_pass',
            'fuel_plugin.tests.functional.dummy_tests.general_test.Dummy_test.test_fast_error': 'fast_error',
            'fuel_plugin.tests.functional.dummy_tests.general_test.Dummy_test.test_fast_fail':  'fast_fail',
            'fuel_plugin.tests.functional.dummy_tests.general_test.Dummy_test.test_long_pass':  'long_pass',
            'fuel_plugin.tests.functional.dummy_tests.general_test.Dummy_test.test_fail_with_step': 'fail_step',
            'fuel_plugin.tests.functional.dummy_tests.stopped_test.dummy_tests_stopped.test_really_long': 'really_long',
            'fuel_plugin.tests.functional.dummy_tests.stopped_test.dummy_tests_stopped.test_not_long_at_all': 'not_long',
            'fuel_plugin.tests.functional.dummy_tests.stopped_test.dummy_tests_stopped.test_one_no_so_long': 'so_long'
        }
        cls.testsets = {
            # "fuel_smoke": None,
            # "fuel_sanity": None,
            "general_test": ['fast_pass', 'fast_error', 'fast_fail', 'long_pass'],
            "stopped_test": ['really_long', 'not_long', 'so_long']
        }

        cls.adapter = adapter(url)
        cls.client = cls.init_client(url, cls.mapping)

    def test_tests_list_with_no_testrun(self):
        '''
        Starts test_run to fill database with needed data.
        Checks wheter test_controller returns only tests
        with no test_run_id field
        '''
        testset = "general_test"
        cluster_id = 1

        self.client.start_testrun(testset, cluster_id)

        r = self.adapter.tests().json()

        self.assertEqual(len(r), len(self.mapping))

    def test_list_testsets(self):
        """Verify that self.testsets are in json response
        """
        json = self.adapter.testsets().json()
        response_testsets = [item['id'] for item in json]
        for testset in self.testsets:
            msg = '"{test}" not in "{response}"'.format(test=testset, response=response_testsets)
            self.assertTrue(testset in response_testsets, msg)

    def test_list_tests(self):
        """Verify that self.tests are in json response
        """
        json = self.adapter.tests().json()
        response_tests = [item['id'] for item in json]

        for test in self.mapping:
            msg = '"{test}" not in "{response}"'.format(test=test.capitalize(), response=response_tests)
            self.assertTrue(test in response_tests, msg)

    def test_run_testset(self):
        """Verify that test status changes in time from running to success
        """
        testset = "general_test"
        cluster_id = 1

        self.client.start_testrun(testset, cluster_id)
        time.sleep(3)

        r = self.client.testruns_last(cluster_id)

        assertions = Response([{'status': 'running',
                                'testset': 'general_test',
                                'tests': [
                                    {'id': 'fast_pass', 'status': 'success', 'name': 'fast pass test',
                                     'description': """        This is a simple always pass test
        """,},
                                    {'id': 'long_pass', 'status': 'running'},
                                    {'id': 'fail_step', 'message': 'Fake fail message', 'status': 'failure'},
                                    {'id': 'fast_error', 'message': '', 'status': 'error'},
                                    {'id': 'fast_fail', 'message': 'Something goes wroooong', 'status': 'failure'}]}])

        print r
        print assertions

        self.compare(r, assertions)
        time.sleep(10)

        r = self.client.testruns_last(cluster_id)

        assertions.general_test['status'] = 'finished'
        assertions.long_pass['status'] = 'success'

        self.compare(r, assertions)

    def test_stop_testset(self):
        """Verify that long running testrun can be stopped
        """
        testset = "stopped_test"
        cluster_id = 2

        self.client.start_testrun(testset, cluster_id)
        time.sleep(10)
        r = self.client.testruns_last(cluster_id)
        assertions = Response([
            {'status': 'running',
                'testset': 'stopped_test',
                'tests': [
                    {'id': 'not_long', 'status': 'success'},
                    {'id': 'so_long', 'status': 'success'},
                    {'id': 'really_long', 'status': 'running'}]}])

        self.compare(r, assertions)

        self.client.stop_testrun_last(testset, cluster_id)
        r = self.client.testruns_last(cluster_id)

        assertions.stopped_test['status'] = 'finished'
        assertions.really_long['status'] = 'stopped'
        self.compare(r, assertions)

    def test_cant_start_while_running(self):
        """Verify that you can't start new testrun for the same cluster_id while previous run is running"""
        testsets = {"stopped_test": None,
                    "general_test": None}
        cluster_id = 3

        for testset in testsets:
            self.client.start_testrun(testset, cluster_id)
        self.client.testruns_last(cluster_id)

        for testset in testsets:
            r = self.client.start_testrun(testset, cluster_id)

            msg = "Response {0} is not empty when you try to start testrun" \
                " with testset and cluster_id that are already running".format(r)

            self.assertTrue(r.is_empty, msg)

    def test_start_many_runs(self):
        """Verify that you can start 20 testruns in a row with different cluster_id"""
        testset = "general_test"

        for cluster_id in range(100, 105):
            r = self.client.start_testrun(testset, cluster_id)
            msg = '{0} was empty'.format(r.request)
            self.assertFalse(r.is_empty, msg)

        '''TODO: Rewrite assertions to verity that all 5 testruns ended with appropriate status'''

    def test_run_single_test(self):
        """Verify that you can run individual tests from given testset"""
        testset = "general_test"
        tests = ['fuel_plugin.tests.functional.dummy_tests.general_test.Dummy_test.test_fast_pass',
                 'fuel_plugin.tests.functional.dummy_tests.general_test.Dummy_test.test_fast_fail']
        cluster_id = 50

        r = self.client.start_testrun_tests(testset, tests, cluster_id)
        assertions = Response([
            {'status': 'running',
             'testset': 'general_test',
             'tests': [
                {'status': 'disabled', 'id': 'fast_error'},
                {'status': 'wait_running', 'id': 'fast_fail'},
                {'status': 'wait_running', 'id': 'fast_pass'},
                {'status': 'disabled', 'id': 'long_pass'}]}])

        self.compare(r, assertions)
        time.sleep(2)

        r = self.client.testruns_last(cluster_id)
        assertions.general_test['status'] = 'finished'
        assertions.fast_fail['status'] = 'failure'
        assertions.fast_pass['status'] = 'success'
        self.compare(r, assertions)

    def test_single_test_restart(self):
        """Verify that you restart individual tests for given testrun"""
        testset = "general_test"
        tests = ['fuel_plugin.tests.functional.dummy_tests.general_test.Dummy_test.test_fast_pass',
                 'fuel_plugin.tests.functional.dummy_tests.general_test.Dummy_test.test_fast_fail']
        cluster_id = 60

        self.client.run_testset_with_timeout(testset, cluster_id, 10)

        r = self.client.restart_tests_last(testset, tests, cluster_id)
        assertions = Response([
            {'status': 'running',
                'testset': 'general_test',
                'tests': [
                    {'id': 'fast_pass',  'status': 'wait_running'},
                    {'id': 'long_pass',  'status': 'success'},
                    {'id': 'fast_error', 'status': 'error'},
                    {'id': 'fast_fail',  'status': 'wait_running'}]}])

        self.compare(r, assertions)
        time.sleep(5)

        r = self.client.testruns_last(cluster_id)
        assertions.general_test['status'] = 'finished'
        assertions.fast_pass['status'] = 'success'
        assertions.fast_fail['status'] = 'failure'

        self.compare(r, assertions)

    def test_restart_combinations(self):
        """Verify that you can restart both tests that ran and did not run during single test start"""
        testset = "general_test"
        tests = ['fuel_plugin.tests.functional.dummy_tests.general_test.Dummy_test.test_fast_pass',
                 'fuel_plugin.tests.functional.dummy_tests.general_test.Dummy_test.test_fast_fail']
        disabled_test = ['fuel_plugin.tests.functional.dummy_tests.general_test.Dummy_test.test_fast_error', ]
        cluster_id = 70

        self.client.run_with_timeout(testset, tests, cluster_id, 70)
        self.client.restart_with_timeout(testset, tests, cluster_id, 10)

        r = self.client.restart_tests_last(testset, disabled_test, cluster_id)
        assertions = Response([
            {'status': 'running',
             'testset': 'general_test',
             'tests': [
            {'status': 'wait_running', 'id': 'fast_error'},
            {'status': 'failure', 'id': 'fast_fail'},
            {'status': 'success', 'id': 'fast_pass'},
            {'status': 'disabled', 'id': 'long_pass'}]}])
        self.compare(r, assertions)
        time.sleep(5)

        r = self.client.testruns_last(cluster_id)
        assertions.general_test['status'] = 'finished'
        assertions.fast_error['status'] = 'error'
        self.compare(r, assertions)

    def test_cant_restart_during_run(self):
        testset = 'general_test'
        tests = ['fuel_plugin.tests.functional.dummy_tests.general_test.Dummy_test.test_fast_pass',
                 'fuel_plugin.tests.functional.dummy_tests.general_test.Dummy_test.test_fast_fail',
                 'fuel_plugin.tests.functional.dummy_tests.general_test.Dummy_test.test_fast_pass']
        cluster_id = 999

        self.client.start_testrun(testset, cluster_id)
        time.sleep(2)

        r = self.client.restart_tests_last(testset, tests, cluster_id)
        msg = 'Response was not empty after trying to restart running testset:\n {0}'.format(r.request)
        self.assertTrue(r.is_empty, msg)

