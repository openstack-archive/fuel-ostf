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

import requests
import time

from oslo.serialization import jsonutils


class TestingAdapterClient(object):
    def __init__(self, url):
        self.url = url

    def _request(self, method, url, data=None):
        headers = {'content-type': 'application/json'}

        ostf_os_access_creds = {
            'ostf_os_username': 'ostf',
            'ostf_os_password': 'ostf',
            'ostf_os_tenant_name': 'ostf'
        }

        if data:
            for data_el in data:
                if 'metadata' in data_el:
                    data_el['metadata']['ostf_os_access_creds'] = \
                        ostf_os_access_creds
                else:
                    data_el['ostf_os_access_creds'] = ostf_os_access_creds

            data = jsonutils.dumps({'objects': data})

        r = requests.request(
            method,
            url,
            data=data,
            headers=headers,
            timeout=30.0
        )

        if 2 != r.status_code / 100:
            raise AssertionError(
                '{method} "{url}" responded with '
                '"{code}" status code'.format(
                    method=method.upper(),
                    url=url, code=r.status_code)
            )
        return r

    def testsets(self, cluster_id):
        url = ''.join(
            [self.url, '/testsets/', str(cluster_id)]
        )
        return self._request('GET', url)

    def tests(self, cluster_id):
        url = ''.join(
            [self.url, '/tests/', str(cluster_id)]
        )
        return self._request('GET', url)

    def testruns(self):
        url = ''.join(
            [self.url, '/testruns/']
        )
        return self._request('GET', url)

    def testruns_last(self, cluster_id):
        url = ''.join([self.url, '/testruns/last/',
                       str(cluster_id)])
        return self._request('GET', url)

    def start_testrun(self, testset, cluster_id):
        return self.start_testrun_tests(testset, [], cluster_id)

    def start_testrun_tests(self, testset, tests, cluster_id):
        url = ''.join([self.url, '/testruns'])
        data = [
            {
                'testset': testset,
                'tests': tests,
                'metadata': {'cluster_id': str(cluster_id)}
            }
        ]
        return self._request('POST', url, data)

    def start_multiple_testruns(self, testsets, cluster_id):
        url = ''.join([self.url, '/testruns'])
        data = [
            {
                'testset': testset,
                'tests': [],
                'metadata': {'cluster_id': str(cluster_id)}
            }
            for testset in testsets
        ]
        return self._request('POST', url, data)

    def stop_testrun(self, testrun_id):
        url = ''.join([self.url, '/testruns'])
        data = [
            {
                "id": testrun_id,
                "status": "stopped"
            }
        ]
        return self._request("PUT", url, data)

    def stop_testrun_last(self, testset, cluster_id):
        latest = self.testruns_last(cluster_id).json()
        testrun_id = [
            item['id'] for item in latest
            if item['testset'] == testset
        ][0]
        return self.stop_testrun(testrun_id)

    def restart_tests(self, tests, testrun_id):
        url = ''.join([self.url, '/testruns'])
        data = [
            {
                'id': str(testrun_id),
                'tests': tests,
                'status': 'restarted'
            }
        ]
        return self._request('PUT', url, data)

    def restart_tests_last(self, testset, tests, cluster_id):
        latest = self.testruns_last(cluster_id).json()
        testrun_id = [
            item['id'] for item in latest
            if item['testset'] == testset
        ][0]
        return self.restart_tests(tests, testrun_id)

    def _with_timeout(self, action, testset, cluster_id,
                      timeout, polling=5, polling_hook=None):
        start_time = time.time()
        decoded_json = action().json()

        if decoded_json == [{}]:
            self.stop_testrun_last(testset, cluster_id)
            time.sleep(1)
            action()

        while time.time() - start_time <= timeout:
            time.sleep(polling)

            current_response = self.testruns_last(cluster_id)
            if polling_hook:
                polling_hook(current_response)
            current_status, current_tests = \
                [(item['status'], item['tests']) for item
                 in current_response.json() if item['testset'] == testset][0]

            if current_status == 'finished':
                break
        else:
            stopped_response = self.stop_testrun_last(testset, cluster_id)
            if polling_hook:
                polling_hook(stopped_response)
            stopped_response = self.testruns_last(cluster_id)
            stopped_status = [
                item['status'] for item in stopped_response.json()
                if item['testset'] == testset
            ][0]

            msg = '{0} is still in {1} state. Now the state is {2}'.format(
                testset, current_status, stopped_status)
            msg_tests = '\n'.join(
                [
                    '{0} -> {1}, {2}'.format(
                        item['id'], item['status'], item['taken']
                    )
                    for item in current_tests
                ]
            )

            raise AssertionError('\n'.join([msg, msg_tests]))
        return current_response

    def run_with_timeout(self, testset, tests, cluster_id, timeout, polling=5,
                         polling_hook=None):
        action = lambda: self.start_testrun_tests(testset, tests, cluster_id)
        return self._with_timeout(action, testset, cluster_id, timeout,
                                  polling, polling_hook)

    def run_testset_with_timeout(self, testset, cluster_id, timeout,
                                 polling=5, polling_hook=None):
        return self.run_with_timeout(testset, [], cluster_id, timeout,
                                     polling, polling_hook)

    def restart_with_timeout(self, testset, tests, cluster_id, timeout):
        action = lambda: self.restart_tests_last(testset, tests, cluster_id)
        return self._with_timeout(action, testset, cluster_id, timeout)
