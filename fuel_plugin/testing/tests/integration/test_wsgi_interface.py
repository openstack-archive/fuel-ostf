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
import mock
from webtest import TestApp

from fuel_plugin.ostf_adapter.storage import models
from fuel_plugin.ostf_adapter.wsgi import app
from fuel_plugin.testing.tests import base


class WsgiInterfaceTest(base.BaseWSGITest):

    def setUp(self):
        super(WsgiInterfaceTest, self).setUp()

        self.app = TestApp(app.setup_app())

    def test_get_all_tests(self):
        cluster_id = 1
        self.mock_api_for_cluster(cluster_id)
        self.app.get('/v1/tests/{0}'.format(cluster_id))

    def test_get_all_testsets(self):
        cluster_id = 1
        self.mock_api_for_cluster(cluster_id)
        self.app.get('/v1/testsets/{0}'.format(cluster_id))

    def test_get_one_testruns(self):
        self.app.get('/v1/testruns/1')

    def test_get_all_testruns(self):
        self.app.get('/v1/testruns')

    @mock.patch.object(models.TestRun, 'start')
    def test_post_testruns(self, mstart):
        self.mock_api_for_cluster(3)
        self.mock_api_for_cluster(4)

        testruns = [
            {
                'testset': 'general_test',
                'metadata': {'cluster_id': 3}
            },
            {
                'testset': 'general_test',
                'metadata': {'cluster_id': 4}
            }
        ]

        self.request_mock.body = json.dumps(testruns)
        mstart.return_value = {}
        self.app.post_json('/v1/testruns', testruns)

    def test_put_testruns(self):
        testruns = [
            {
                'id': 2,
                'metadata': {'cluster_id': 3},
                'status': 'non_exist'
            },
            {
                'id': 1,
                'metadata': {'cluster_id': 4},
                'status': 'non_exist'
            }
        ]

        self.request_mock.body = json.dumps(testruns)
        self.request_mock.storage.get_test_run.return_value = \
            mock.MagicMock(frontend={})
        self.app.put_json('/v1/testruns', testruns)

    def test_get_last_testruns(self):
        cluster_id = 1
        self.mock_api_for_cluster(cluster_id)
        self.app.get('/v1/testruns/last/{0}'.format(cluster_id))
