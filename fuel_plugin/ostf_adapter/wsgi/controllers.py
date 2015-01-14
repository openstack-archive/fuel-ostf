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
import logging

from oslo.config import cfg
from pecan import abort
from pecan import expose
from pecan import request
from pecan import rest
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from fuel_plugin.ostf_adapter import mixins
from fuel_plugin.ostf_adapter.storage import models


LOG = logging.getLogger(__name__)


class BaseRestController(rest.RestController):
    def _handle_get(self, method, remainder):
        if len(remainder):
            method_name = remainder[0]
            if method.upper() in self._custom_actions.get(method_name, []):
                controller = self._find_controller(
                    'get_%s' % method_name,
                    method_name
                )
                if controller:
                    return controller, remainder[1:]
        return super(BaseRestController, self)._handle_get(method, remainder)


class TestsetsController(BaseRestController):

    @expose('json')
    def get(self, cluster):
        mixins.discovery_check(request.session, cluster, request.token)

        needed_testsets = request.session\
            .query(models.ClusterTestingPattern.test_set_id)\
            .filter_by(cluster_id=cluster)

        test_sets = request.session.query(models.TestSet)\
            .filter(models.TestSet.id.in_(needed_testsets))\
            .order_by(models.TestSet.test_runs_ordering_priority)\
            .all()

        if test_sets:
            return [item.frontend for item in test_sets]
        return {}


class TestsController(BaseRestController):

    @expose('json')
    def get(self, cluster):
        mixins.discovery_check(request.session, cluster, request.token)
        needed_tests_list = request.session\
            .query(models.ClusterTestingPattern.tests)\
            .filter_by(cluster_id=cluster)

        result = []
        for tests in needed_tests_list:
            tests_to_return = request.session.query(models.Test)\
                .filter(models.Test.name.in_(tests[0]))\
                .all()

            result.extend(tests_to_return)

        result.sort(key=lambda test: test.name)

        if result:
            return [item.frontend for item in result]

        return {}


class TestrunsController(BaseRestController):

    _custom_actions = {
        'last': ['GET'],
    }

    @expose('json')
    def get_all(self):
        test_runs = request.session.query(models.TestRun).all()

        return [item.frontend for item in test_runs]

    @expose('json')
    def get_one(self, test_run_id):
        test_run = request.session.query(models.TestRun)\
            .filter_by(id=test_run_id).first()
        if test_run and isinstance(test_run, models.TestRun):
            return test_run.frontend
        return {}

    @expose('json')
    def get_last(self, cluster_id):
        test_run_ids = request.session.query(func.max(models.TestRun.id)) \
            .group_by(models.TestRun.test_set_id)\
            .filter_by(cluster_id=cluster_id)

        test_runs = request.session.query(models.TestRun)\
            .options(joinedload('tests'))\
            .filter(models.TestRun.id.in_(test_run_ids))

        return [item.frontend for item in test_runs]

    @expose('json')
    def post(self):
        test_runs = json.loads(request.body)
        if 'objects' in test_runs:
            test_runs = test_runs['objects']

        # Discover tests for all clusters in request
        clusters_ids = []
        nedded_testsets = set()
        for test_run in test_runs:
            cluster_id = test_run['metadata']['cluster_id']
            if cluster_id not in clusters_ids:
                clusters_ids.append(cluster_id)
                mixins.discovery_check(request.session,
                                       cluster_id,
                                       request.token)
            nedded_testsets.add(test_run['testset'])
        # Validate testsets from request
        test_sets = set([testset.id for testset in request.
                        session.query(models.TestSet).all()])
        if nedded_testsets - test_sets:
            abort(400)

        res = []
        for test_run in test_runs:
            test_set = test_run['testset']
            metadata = test_run['metadata']
            tests = test_run.get('tests', [])

            test_set = models.TestSet.get_test_set(
                request.session,
                test_set
            )

            test_run = models.TestRun.start(
                request.session,
                test_set,
                metadata,
                tests,
                cfg.CONF.adapter.dbpath,
                token=request.token
            )

            res.append(test_run)

        return res

    @expose('json')
    def put(self):
        test_runs = json.loads(request.body)
        if 'objects' in test_runs:
            test_runs = test_runs['objects']

        data = []
        with request.session.begin(subtransactions=True):
            for test_run in test_runs:
                status = test_run.get('status')
                tests = test_run.get('tests', [])
                ostf_os_access_creds = test_run.get('ostf_os_access_creds')

                test_run = models.TestRun.get_test_run(request.session,
                                                       test_run['id'])
                if status == 'stopped':
                    data.append(test_run.stop(request.session))
                elif status == 'restarted':
                    data.append(test_run.restart(request.session,
                                                 cfg.CONF.adapter.dbpath,
                                                 ostf_os_access_creds,
                                                 tests=tests,
                                                 token=request.token))
        return data
