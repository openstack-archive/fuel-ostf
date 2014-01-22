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
        #StoragePlugin is dependent on this data
        self.nailgun_credentials = {'host': conf.nailgun.host,
                                    'port': conf.nailgun.port}

        self.task_registry = dict()

    def run(self, testruns_chains):
        session = engine.get_session()

        for cluster_id in testruns_chains:
            for exec_type in ['dependent_tests', 'independent_tests']:
                subtasks_list = []
                for testset_data in testruns_chains[cluster_id][exec_type]:

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

                    subtask = ostf_celery_app.run_test_task.si(
                        test_run.id, test_run.cluster_id,
                        self.nailgun_credentials, argv_add
                    )

                    subtask_data = dict(subtask=subtask,
                                        test_run_id=test_run.id)

                    subtasks_list.append(subtask_data)

                if exec_type == 'dependent_tests':
                    self.task_registry.update(
                        {
                            tuple([task_data['test_run_id'] for task_data
                                   in subtasks_list]):
                            chain(*[task_data['subtask']
                                    for task_data in subtasks_list])
                            .apply_async()
                        }
                    )
                elif exec_type == 'independent_tests':
                    for task_data in subtasks_list:
                        self.task_registry.update(
                            {
                                (task_data['test_run_id'],):
                                task_data['subtask'].apply_async()
                            }
                        )

    def kill(self, test_run_id, cluster_id, cleanup=None):
        session = engine.get_session()

        for task_identity in self.task_registry:
            if test_run_id in task_identity:
                self.task_registry[task_identity].revoke(signal='SIGTERM',
                                                         terminate=True)

                test_run = session.query(models.TestRun)\
                    .filter_by(id=test_run_id)\
                    .one()

                if test_run.status == 'running':
                    if cleanup:
                        ostf_celery_app.clean_up.delay(
                            test_run_id, cluster_id,
                            cleanup, self.nailgun_credentials
                        )

                    models.TestRun.update_test_run(
                        session, test_run_id, status='finished'
                    )

                    models.Test.update_running_tests(
                        session, test_run_id, status='stopped'
                    )
