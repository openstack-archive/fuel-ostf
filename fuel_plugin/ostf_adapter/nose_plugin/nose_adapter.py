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

from celery import chain

from pecan import conf
from fuel_plugin.ostf_adapter.nose_plugin import nose_utils
from fuel_plugin.ostf_adapter.storage import engine, models
from fuel_plugin.ostf_adapter.celery_app import ostf_celery_app


LOG = logging.getLogger(__name__)


class NoseDriver(object):

    def __init__(self):
        LOG.warning('Initializing Nose Driver')
        self._named_threads = {}

    def check_current_running(self, unique_id):
        return unique_id in self._named_threads

    def run(self, testruns_chains):
        session = engine.get_session()
        #StoragePlugin is dependent on this data
        nailgun_credentials = {'host': conf.nailgun.host,
                               'port': conf.nailgun.port}

        def _prepare_tasks_args(testruns_chains, exec_type,
                                session, nailgun_credentials):
            tasks_args_list = []
            for cluster_id in testruns_chains:
                #borders list of args for test runs that
                #must be executed for particular cluster
                cluster_testruns_args_list = []

                for testset_data in \
                        testruns_chains[cluster_id][exec_type]:

                    test_run = session.query(models.TestRun)\
                        .filter_by(test_set_id=testset_data['testset'])\
                        .filter_by(cluster_id=cluster_id)\
                        .filter_by(status='running')\
                        .one()

                    tests = testset_data['tests'] or test_run.enabled_tests
                    if tests:
                        argv_add = [
                            nose_utils.modify_test_name_for_nose(test)
                            for test in tests
                        ]

                    else:
                        test_set = session.query(models.TestSet)\
                            .filter_by(id=testset_data['testset'])\
                            .one()
                        argv_add = [test_set.test_path] + \
                            test_set.additional_arguments

                    #built chain of tasks
                    cluster_testruns_args_list.append(
                        [test_run.id, test_run.cluster_id,
                         nailgun_credentials, argv_add]
                    )

                tasks_args_list.append(cluster_testruns_args_list)

            return tasks_args_list

        #make chains for solo workers
        dependent_tasks_args = \
            _prepare_tasks_args(
                testruns_chains,
                'dependent_tests',
                session,
                nailgun_credentials
            )

        for cluster_task_args in dependent_tasks_args:
            chain(
                *[
                    ostf_celery_app.run_test_task.si(*args)
                    for args in cluster_task_args
                ]
            ).apply_async()

        #process independent workers
        independent_tasks_args = \
            _prepare_tasks_args(
                testruns_chains,
                'independent_tests',
                session,
                nailgun_credentials
            )

        for cluster_task_args in independent_tasks_args:
            for task_args in cluster_task_args:
                ostf_celery_app.run_test_task.apply_async(
                    args=task_args
                )

    def kill(self, test_run_id, cluster_id, cleanup=None):
        session = engine.get_session()
        if test_run_id in self._named_threads:

            try:
                self._named_threads[test_run_id].terminate()
            except OSError as e:
                if e.errno != os.errno.ESRCH:
                    raise

                LOG.warning(
                    'There is no process for test_run with following id - %s',
                    test_run_id
                )

            self._named_threads.pop(test_run_id, None)

            if cleanup:
                nose_utils.run_proc(
                    self._clean_up,
                    test_run_id,
                    cluster_id,
                    cleanup)
            else:
                models.TestRun.update_test_run(
                    session, test_run_id, status='finished')

            return True
        return False

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
