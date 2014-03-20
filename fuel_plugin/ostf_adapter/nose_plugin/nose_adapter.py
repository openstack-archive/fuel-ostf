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
import signal

from pecan import conf
from fuel_plugin.ostf_adapter.nose_plugin import nose_test_runner
from fuel_plugin.ostf_adapter.nose_plugin import nose_utils
from fuel_plugin.ostf_adapter.storage import engine, models

from fuel_plugin.ostf_adapter.nose_plugin import nose_storage_plugin


LOG = logging.getLogger(__name__)


class InterruptTestRunException(KeyboardInterrupt):
    ''' Current class exception is used for cleanup action
    as KeyboardInterrupt is the only exception that is reraised by
    unittest (and nose correspondingly) into outside environment
    '''
    pass


def start_testrun(dbpath, test_run_id, tests):
    with engine.contexted_session(dbpath) as session:
        test_run = session.query(models.TestRun)\
            .filter_by(id=test_run_id)\
            .one()
        test_set = session.query(models.TestSet)\
            .filter_by(id=test_run.test_set_id)\
            .one()

        tests = tests or test_run.enabled_tests
        if tests:
            argv_add = [nose_utils.modify_test_name_for_nose(test)
                        for test in tests]
        else:
            argv_add = [test_set.test_path] + test_set.additional_arguments

        allow_to_run = not bool(
            session.query(models.TestRun)
            .filter(models.TestRun.cluster_id == test_run.cluster_id)
            .filter(models.TestRun.pid is not None)
            .filter(
                models.TestRun.test_set_id.in_(test_set.exclusive_testsets)
            )
            .all()
        )

        if allow_to_run:
            test_run.pid = nose_utils.run_proc(run_tests,
                                               dbpath,
                                               test_run.id,
                                               test_run.cluster_id,
                                               argv_add).pid
            return True
        else:
            return False


def run_tests(dbpath, test_run_id, cluster_id, argv_add):
    cleanup_flag = False

    def raise_exception_handler(signum, stack_frame):
        raise InterruptTestRunException()
    signal.signal(signal.SIGUSR1, raise_exception_handler)

    with engine.contexted_session(dbpath) as session:
        try:
            nose_test_runner.SilentTestProgram(
                addplugins=[nose_storage_plugin.StoragePlugin(
                    session, test_run_id, str(cluster_id))],
                exit=False,
                argv=['ostf_tests'] + argv_add)

        except InterruptTestRunException:
            testset_id = session.query(models.TestRun.test_set_id)\
                .filter_by(id=test_run_id)\
                .scalar()
            cleanup = session.query(models.TestSet.cleanup_path)\
                .filter_by(id=testset_id)\
                .scalar()

            if cleanup:
                cleanup_flag = True

        except Exception:
            LOG.exception('Test run ID: %s', test_run_id)
        finally:
            updated_data = {'status': 'finished',
                            'pid': None}

            models.TestRun.update_test_run(
                session, test_run_id, updated_data)

            if cleanup_flag:
                _clean_up(session, test_run_id, cluster_id, cleanup)


def _clean_up(session, test_run_id, cluster_id, cleanup):
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
