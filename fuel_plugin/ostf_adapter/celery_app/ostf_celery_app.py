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

import celery
import logging
import os

import celeryconfig

from fuel_plugin.ostf_adapter.storage import engine, models
from fuel_plugin.ostf_adapter.nose_plugin import nose_storage_plugin
from fuel_plugin.ostf_adapter.nose_plugin import nose_test_runner


LOG = logging.getLogger(__name__)


APP = celery.Celery('ostf_celery_app',
                    broker='amqp://ostf:ostf@localhost/ostf',
                    backend='amqp')

APP.config_from_object(celeryconfig)


@APP.task
def run_test_task(test_run_id, cluster_id, nailgun_credentials, argv_add):
    '''Starts testrun via custom nose plugin
    '''
    session = engine.get_session()
    try:
        nose_test_runner.SilentTestProgram(
            addplugins=[nose_storage_plugin.StoragePlugin(
                test_run_id, str(cluster_id), nailgun_credentials)],
            exit=False,
            argv=['ostf_tests'] + argv_add)
    except Exception:
        LOG.exception('Test run ID: %s', test_run_id)
    finally:
        models.TestRun.update_test_run(
            session, test_run_id, status='finished')


@APP.task
def clean_up(test_run_id, cluster_id, cleanup, nailgun_credentials):
    session = engine.get_session()

    #need for performing proper cleaning up for current cluster
    cluster_deployment_info = \
        session.query(models.ClusterState.deployment_tags)\
        .filter_by(id=cluster_id)\
        .scalar()

    try:
        module_obj = __import__(cleanup, -1)

        os.environ['NAILGUN_HOST'] = str(nailgun_credentials['host'])
        os.environ['NAILGUN_PORT'] = str(nailgun_credentials['port'])
        os.environ['CLUSTER_ID'] = str(cluster_id)

        module_obj.cleanup.cleanup(cluster_deployment_info)

    except Exception:
        LOG.exception(
            'Cleanup error. Test Run ID %s. Cluster ID %s',
            test_run_id,
            cluster_id
        )
