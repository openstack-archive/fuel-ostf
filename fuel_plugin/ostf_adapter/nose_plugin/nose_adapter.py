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
import logging
from pecan import conf

from fuel_plugin.ostf_adapter.nose_plugin import nose_storage_plugin
from fuel_plugin.ostf_adapter.nose_plugin import nose_test_runner
from fuel_plugin.ostf_adapter.nose_plugin import nose_utils
from fuel_plugin.ostf_adapter.storage import storage_utils, engine, models


LOG = logging.getLogger(__name__)


class NoseDriver(object):
    def __init__(self):
        LOG.warning('Initializing Nose Driver')
        self._named_threads = {}
        session = engine.get_session()
        storage_utils.update_all_running_test_runs(session)

    def check_current_running(self, unique_id):
        return unique_id in self._named_threads

    def run(self):
        session = engine.get_session()
        test_runs_to_run_first = session.query(models.TestRun)\
            .filter_by(status='running')\
            .all()

        for test_run in test_runs_to_run_first:
            tests = test_run.enabled_tests
            if tests:
                argv_add = [
                    models.Test.modify_test_name_for_nose(test) for test in
                    tests
                ]

            else:
                test_set = session.query(models.TestSet)\
                    .filter_by(id=test_run.test_set_id)\
                    .one()

                argv_add = test_set.run_test_additional_args

            deffered_test_runs = session.query(models.TestRun)\
                .filter_by(cluster_id=test_run.cluster_id)\
                .filter_by(status='deffered')\
                .all()

            named_threads_key = tuple(
                [test_run.id] + [tr.id for tr in deffered_test_runs]
            )
            self._named_threads[named_threads_key] = nose_utils.run_proc(
                self._run_tests, test_run.id, test_run.cluster_id, argv_add)

    def _run_tests(self, test_run_id, cluster_id, argv_add):
        session = engine.get_session()
        try:
            nose_test_runner.SilentTestProgram(
                addplugins=[nose_storage_plugin.StoragePlugin(
                    test_run_id, str(cluster_id))],
                exit=False,
                argv=['ostf_tests'] + argv_add)
            #self._named_threads.pop(int(test_run_id), None)
        except Exception:
            LOG.exception('Test run ID: %s', test_run_id)
        finally:
            models.TestRun.update_test_run(
                session, test_run_id, status='finished')

            #run deffered test_runs
            deffered_test_runs = session.query(models.TestRun)\
                .filter_by(status='deffered')\
                .filter_by(cluster_id=cluster_id)\
                .all()

            if deffered_test_runs:
                for test_run in deffered_test_runs:
                    models.TestRun.update_test_run(session, test_run.id,
                                                   status='running')
                    tests = test_run.enabled_tests

                    if tests:
                        argv_add = [
                            models.Test.modify_test_name_for_nose(test)
                            for test in tests
                        ]

                    else:
                        test_set = session.query(models.TestSet)\
                            .filter_by(id=test_run.test_set_id)\
                            .one()

                        argv_add = test_set.run_test_additional_args

                    self._run_tests(test_run.id, cluster_id, argv_add)

    def kill(self, test_run_id, cluster_id):
        session = engine.get_session()

        threads_keys = self._named_threads.keys()
        for test_runs_key in threads_keys:
            if test_run_id in test_runs_key:

                try:
                    self._named_threads[test_runs_key].terminate()
                except OSError as e:
                    if e.errno != os.errno.ESRCH:
                        raise

                    LOG.warning(
                        'There is no process for test_run with id-%s',
                        test_runs_key
                    )

                test_runs_data = session.query(models.TestRun)\
                    .filter(models.TestRun.id.in_(test_runs_key))\
                    .all()

                for tr in test_runs_data:
                    if tr.status == 'deffered':
                        models.TestRun.update_test_run(session, tr.id,
                                                       status='finished')
                        models.Test.update_running_tests(session,
                                                         tr.id,
                                                         status='stopped')
                    elif tr.status == 'running':
                        test_set = session.query(models.TestSet)\
                            .filter_by(id=tr.test_set_id)\
                            .one()

                        if test_set.cleanup_path:
                            nose_utils.run_proc(self._clean_up, tr.id,
                                                tr.cluster_id,
                                                test_set.cleanup_path)
                        else:
                            models.TestRun.update_test_run(session,
                                                           tr.id,
                                                           status='finished')

                        models.Test.update_running_tests(session,
                                                         tr.id,
                                                         status='stopped')

                self._named_threads.pop(test_runs_key, None)

    def _clean_up(self, test_run_id, cluster_id, cleanup):
        session = engine.get_session()

        #need for performing proper cleaning up for current cluster
        cluster_deployment_info = \
            session.query(models.ClusterState.deployment_tags)\
            .filter_by(id=cluster_id)\
            .scalar()

        try:
            module_obj = __import__(cleanup, -1)

            os.environ['NAILGUN_HOST'] = str(conf.nailgun.host)
            os.environ['NAILGUN_PORT'] = str(conf.nailgun.port)
            os.environ['CLUSTER_ID'] = str(cluster_id)

            module_obj.cleanup.cleanup(cluster_deployment_info)

        except Exception:
            LOG.exception(
                'Cleanup error. Test Run ID %s. Cluster ID %s',
                test_run_id,
                cluster_id
            )

        finally:
            models.TestRun.update_test_run(
                session, test_run_id, status='finished')
