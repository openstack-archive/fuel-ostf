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

from fuel_plugin.tests.functional.base import BaseAdapterTest


class ScenarioTests(BaseAdapterTest):
    @classmethod
    def setUpClass(cls):

        url = 'http://0.0.0.0:8989/v1'
        mapping = {}

        cls.client = cls.init_client(url, mapping)

    def test_random_scenario(self):
        testset = "fuel_sanity"
        cluster_id = 3
        tests = []
        timeout = 60

        from pprint import pprint

        for i in range(1):
            r = self.client.run_with_timeout(
                testset,
                tests,
                cluster_id,
                timeout
            )

            pprint([item for item in r.test_sets[testset]['tests']])
            if r.fuel_sanity['status'] == 'stopped':
                running_tests = [test for test in r._tests
                                 if r._tests[test]['status'] is 'stopped']
                print "restarting: ", running_tests

                result = self.client.restart_with_timeout(
                    testset,
                    running_tests,
                    cluster_id,
                    timeout
                )
                print 'Restart', result

    def test_run_fuel_sanity(self):
        testset = "fuel_sanity"
        cluster_id = 3
        tests = []

        timeout = 240

        r = self.client.run_with_timeout(testset, tests, cluster_id, timeout)
        for item in r.fuel_sanity['tests']:
            print item['id'].split('.').pop(), item
        self.assertEqual(r.fuel_sanity['status'], 'finished')

    def test_run_fuel_smoke(self):
        testset = "fuel_smoke"
        cluster_id = 3
        tests = []
        timeout = 900

        r = self.client.run_with_timeout(testset, tests, cluster_id, timeout)
        for item in r.fuel_sanity['tests']:
            print item['id'].split('.').pop(), item
        self.assertEqual(r.fuel_smoke['status'], 'finished')
