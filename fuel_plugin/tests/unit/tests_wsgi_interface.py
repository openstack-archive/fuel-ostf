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
import json

from webtest import TestApp

from fuel_plugin.ostf_adapter.wsgi import app


#@patch('fuel_plugin.ostf_adapter.wsgi.controllers.request')
@unittest2.skip("Fix is needed")
class WsgiInterfaceTests(unittest2.TestCase):

    def setUp(self):
        self.app = TestApp(app.setup_app())

    def test_get_all_tests(self, request):
        self.app.get('/v1/tests')

    def test_get_one_test(self, request):
        self.assertRaises(NotImplementedError,
                          self.app.get,
                          '/v1/tests/1')

    def test_get_all_testsets(self, request):
        self.app.get('/v1/testsets')

    def test_get_one_testset(self, request):
        self.app.get('/v1/testsets/plugin_test')

    def test_get_one_testruns(self, request):
        self.app.get('/v1/testruns/1')

    def test_get_all_testruns(self, request):
        self.app.get('/v1/testruns')

    @patch('fuel_plugin.ostf_adapter.wsgi.controllers.models')
    def test_post_testruns(self, models, request):
        testruns = [
            {'testset': 'test_simple',
             'metadata': {'cluster_id': 3}
            },
            {'testset': 'test_simple',
             'metadata': {'cluster_id': 4}
            }]
        request.body = json.dumps(testruns)
        models.TestRun.start.return_value = {}
        self.app.post_json('/v1/testruns', testruns)

    def test_put_testruns(self, request):
        testruns = [
            {'id': 2,
             'metadata': {'cluster_id': 3},
             'status': 'non_exist'
            },
            {'id': 1,
             'metadata': {'cluster_id': 4},
             'status': 'non_exist'
            }]
        request.body = json.dumps(testruns)
        request.storage.get_test_run.return_value = MagicMock(frontend={})
        self.app.put_json('/v1/testruns', testruns)

    def test_get_last_testruns(self, request):
        self.app.get('/v1/testruns/last/101')
