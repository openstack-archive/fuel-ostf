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


import requests
from pecan import conf
from sqlalchemy.orm import joinedload

from fuel_plugin.ostf_adapter.storage import models, engine
from fuel_plugin.ostf_adapter.nose_plugin import nose_utils

REQ_SES = requests.Session()
REQ_SES.trust_env = False

URL = 'http://{0}:{1}/{2}'
NAILGUN_API_URL = 'api/clusters/{0}'

TEST_REPOSITORY = []


def clean_db(eng):
    conn = eng.connect()

    conn.execute('delete from cluster_testing_pattern;')
    conn.execute('delete from cluster_state;')
    conn.execute('delete from test_sets;')

    conn.close()


def cache_test_repository(session):
    with session.begin(subtransactions=True):
        test_repository = session.query(models.TestSet)\
            .options(joinedload('tests'))\
            .all()

        crucial_tests_attrs = ['name', 'deployment_tags']
        for test_set in test_repository:
            data_elem = dict()

            data_elem['test_set_id'] = test_set.id
            data_elem['deployment_tags'] = test_set.deployment_tags
            data_elem['tests'] = []

            for test in test_set.tests:
                test_dict = dict([(attr_name, getattr(test, attr_name))
                                  for attr_name in crucial_tests_attrs])
                data_elem['tests'].append(test_dict)

            TEST_REPOSITORY.append(data_elem)


def discovery_check(session, cluster):
    cluster_deployment_args = _get_cluster_depl_tags(cluster)

    cluster_data = {
        'cluster_id': cluster,
        'deployment_tags': cluster_deployment_args
    }

    with session.begin(subtransactions=True):
        cluster_state = session.query(models.ClusterState)\
            .filter_by(id=cluster_data['cluster_id'])\
            .first()

    if not cluster_state:
        with session.begin(subtransactions=True):
            session.add(
                models.ClusterState(
                    id=cluster_data['cluster_id'],
                    deployment_tags=list(cluster_data['deployment_tags'])
                )
            )

        with session.begin(subtransactions=True):
            _add_cluster_testing_pattern(session, cluster_data)

        return

    old_deployment_tags = cluster_state.deployment_tags
    if set(old_deployment_tags) != cluster_data['deployment_tags']:
        with session.begin(subtransactions=True):
            #delete testruns and their tests if cluster was redeployed
            session.query(models.ClusterTestingPattern)\
                .filter_by(cluster_id=cluster_state.id)\
                .delete()

        #separate block "with" is need here to resolve
        #situation where previous deletion blocks table
        #that is using in following update
        with session.begin(subtransactions=True):
            #make "rediscovering" of testsets for redeployed cluster
            _add_cluster_testing_pattern(session, cluster_data)

            cluster_state.deployment_tags = \
                list(cluster_data['deployment_tags'])

            session.merge(cluster_state)


def _get_cluster_depl_tags(cluster_id):
    cluster_url = NAILGUN_API_URL.format(cluster_id)
    request_url = URL.format(conf.nailgun.host,
                             conf.nailgun.port,
                             cluster_url)

    response = REQ_SES.get(request_url).json()

    deployment_tags = set()

    #info about deployment type and operating system
    mode = 'ha' if 'ha' in response['mode'].lower() else response['mode']
    deployment_tags.add(mode)
    deployment_tags.add(response['release']['operating_system'])

    #networks manager
    network_type = response.get('net_provider', 'nova_network')
    deployment_tags.add(network_type)

    #info about murano/savanna clients installation
    request_url += '/' + 'attributes'
    response = REQ_SES.get(request_url).json()

    additional_components = \
        response['editable'].get('additional_components', dict())

    additional_depl_tags = set()

    comp_names = ['murano', 'savanna', 'heat']

    def processor(comp):
        if comp in comp_names:
            if additional_components.get(comp)\
               and additional_components.get(comp)['value']\
               is True:

                additional_depl_tags.add(comp)

    for comp in comp_names:
        processor(comp)

    if additional_depl_tags:
        deployment_tags.add('additional_components')
        deployment_tags.update(additional_depl_tags)

    return set([tag.lower() for tag in deployment_tags])


def _add_cluster_testing_pattern(session, cluster_data):
    with session.begin(subtransactions=True):
        to_database = []
        for test_set in TEST_REPOSITORY:
            if nose_utils.process_deployment_tags(
                cluster_data['deployment_tags'],
                test_set['deployment_tags']
            ):

                testing_pattern = dict()
                testing_pattern['cluster_id'] = cluster_data['cluster_id']
                testing_pattern['test_set_id'] = test_set['test_set_id']
                testing_pattern['tests'] = []

                for test in test_set['tests']:
                    if nose_utils.process_deployment_tags(
                        cluster_data['deployment_tags'],
                        test['deployment_tags']
                    ):

                        testing_pattern['tests'].append(test['name'])

                to_database.append(
                    models.ClusterTestingPattern(**testing_pattern)
                )

        session.add_all(to_database)
