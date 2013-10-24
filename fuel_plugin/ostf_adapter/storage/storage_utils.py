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

from fuel_plugin.ostf_adapter.storage.simple_cache import TEST_REPOSITORY
from fuel_plugin.ostf_adapter.storage import models
from fuel_plugin.ostf_adapter.nose_plugin.nose_utils import \
    process_deployment_tags


def update_all_running_test_runs(session):
    session.query(models.TestRun). \
        filter_by(status='running'). \
        update({'status': 'finished'}, synchronize_session=False)
    session.query(models.Test). \
        filter(models.Test.status.in_(('running', 'wait_running'))). \
        update({'status': 'stopped'}, synchronize_session=False)


def add_cluster_testing_pattern(session, cluster_data):
    with session.begin(subtransactions=True):
        to_database = []
        for test_set in TEST_REPOSITORY:
            if process_deployment_tags(
                cluster_data['deployment_tags'],
                test_set['deployment_tags']
            ):

                testing_pattern = dict()
                testing_pattern['cluster_id'] = cluster_data['cluster_id']
                testing_pattern['test_set_id'] = test_set['test_set_id']
                testing_pattern['tests'] = []

                for test in test_set['tests']:
                    if process_deployment_tags(
                        cluster_data['deployment_tags'],
                        test['deployment_tags']
                    ):

                        testing_pattern['tests'].append(test['name'])

                to_database.append(
                    models.ClusterTestingPattern(**testing_pattern)
                )

        session.add_all(to_database)
