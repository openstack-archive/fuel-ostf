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

from fuel_plugin.ostf_adapter.wsgi import controllers
from fuel_plugin.ostf_adapter.storage import models


@patch('fuel_plugin.ostf_adapter.wsgi.controllers.request')
class TestTestsController(unittest2.TestCase):

    def setUp(self):
        self.fixtures = [models.Test(), models.Test()]
        self.controller = controllers.TestsController()

    def test_get_all(self, request):
        request.session.query().filter_by().all.return_value = self.fixtures
        res = self.controller.get_all()
        self.assertEqual(res, [f.frontend for f in self.fixtures])


@patch('fuel_plugin.ostf_adapter.wsgi.controllers.request')
class TestTestSetsController(unittest2.TestCase):

    def setUp(self):
        self.fixtures = [models.TestSet(), models.TestSet()]
        self.controller = controllers.TestsetsController()

    def test_get_all(self, request):
        request.session.query().all.return_value = self.fixtures
        res = self.controller.get_all()
        self.assertEqual(res, [f.frontend for f in self.fixtures])


@patch('fuel_plugin.ostf_adapter.wsgi.controllers.request')
class TestTestRunsController(unittest2.TestCase):

    def setUp(self):
        self.fixtures = [models.TestRun(status='finished'),
                         models.TestRun(status='running')]
        self.fixtures[0].test_set = models.TestSet(driver='nose')
        self.storage = MagicMock()
        self.plugin = MagicMock()
        self.session = MagicMock()
        self.controller = controllers.TestrunsController()

    def test_get_all(self, request):
        request.session.query().all.return_value = self.fixtures
        res = self.controller.get_all()
        self.assertEqual(res, [f.frontend for f in self.fixtures])

    def test_get_one(self, request):
        request.session.query().filter_by().first.return_value = \
            self.fixtures[0]
        res = self.controller.get_one(1)
        self.assertEqual(res, self.fixtures[0].frontend)

    @patch('fuel_plugin.ostf_adapter.wsgi.controllers.models')
    def test_post(self, models, request):
        request.storage = self.storage
        testruns = [
            {'testset': 'test_simple',
             'metadata': {'cluster_id': 3}
            },
            {'testset': 'test_simple',
             'metadata': {'cluster_id': 4}
            }]
        request.body = json.dumps(testruns)
        fixtures_iterable = (f.frontend for f in self.fixtures)

        models.TestRun.start.side_effect = \
            lambda *args, **kwargs: fixtures_iterable.next()
        res = self.controller.post()
        self.assertEqual(res, [f.frontend for f in self.fixtures])

    @patch('fuel_plugin.ostf_adapter.wsgi.controllers.models')
    def test_put_stopped(self, models, request):
        request.storage = self.storage
        testruns = [
            {'id': 1,
             'metadata': {'cluster_id': 4},
             'status': 'stopped'
            }]
        request.body = json.dumps(testruns)

        models.TestRun.get_test_run().stop.side_effect = \
            lambda *args, **kwargs: self.fixtures[0].frontend
        res = self.controller.put()
        self.assertEqual(res, [self.fixtures[0].frontend])

    @patch('fuel_plugin.ostf_adapter.wsgi.controllers.models')
    def test_put_restarted(self, models, request):
        request.storage = self.storage
        testruns = [
            {'id': 1,
             'metadata': {'cluster_id': 4},
             'status': 'restarted'
            }]
        request.body = json.dumps(testruns)

        models.TestRun.get_test_run().restart.side_effect = \
            lambda *args, **kwargs: self.fixtures[0].frontend
        res = self.controller.put()
        self.assertEqual(res, [self.fixtures[0].frontend])

    def test_get_last(self, request):
        cluster_id = 1
        request.session.query().group_by().filter_by.return_value = [10, 11]
        request.session.query().options().filter.return_value = self.fixtures
        res = self.controller.get_last(cluster_id)
        self.assertEqual(res, [f.frontend for f in self.fixtures])
