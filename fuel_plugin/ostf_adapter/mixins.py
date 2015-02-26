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

from oslo.config import cfg
import requests
from sqlalchemy.orm import joinedload

from fuel_plugin.ostf_adapter.nose_plugin import nose_utils
from fuel_plugin.ostf_adapter.storage import models


LOG = logging.getLogger(__name__)


TEST_REPOSITORY = []


def delete_db_data(session):
    LOG.info('Starting clean db action.')
    session.query(models.ClusterTestingPattern).delete()
    session.query(models.ClusterState).delete()
    session.query(models.TestSet).delete()

    session.commit()


def cache_test_repository(session):
    test_repository = session.query(models.TestSet)\
        .options(joinedload('tests'))\
        .all()

    crucial_tests_attrs = ['name', 'deployment_tags',
                           'available_since_release']
    for test_set in test_repository:
        data_elem = dict()

        data_elem['test_set_id'] = test_set.id
        data_elem['deployment_tags'] = test_set.deployment_tags
        data_elem['available_since_release'] = test_set.available_since_release
        data_elem['tests'] = []

        for test in test_set.tests:
            test_dict = dict([(attr_name, getattr(test, attr_name))
                              for attr_name in crucial_tests_attrs])
            data_elem['tests'].append(test_dict)

        TEST_REPOSITORY.append(data_elem)


def discovery_check(session, cluster_id, token=None):
    cluster_attrs = _get_cluster_attrs(cluster_id, token=token)

    cluster_data = {
        'id': cluster_id,
        'deployment_tags': cluster_attrs['deployment_tags'],
        'release_version': cluster_attrs['release_version'],
    }

    cluster_state = session.query(models.ClusterState)\
        .filter_by(id=cluster_data['id'])\
        .first()

    if not cluster_state:
        session.add(
            models.ClusterState(
                id=cluster_data['id'],
                deployment_tags=list(cluster_data['deployment_tags'])
            )
        )

        # flush data to db, because _add_cluster_testing_pattern
        # is dependent on it
        session.flush()

        _add_cluster_testing_pattern(session, cluster_data)

        return

    old_deployment_tags = cluster_state.deployment_tags
    if set(old_deployment_tags) != cluster_data['deployment_tags']:
        session.query(models.ClusterTestingPattern)\
            .filter_by(cluster_id=cluster_state.id)\
            .delete()

        _add_cluster_testing_pattern(session, cluster_data)

        cluster_state.deployment_tags = \
            list(cluster_data['deployment_tags'])

        session.merge(cluster_state)


def _get_cluster_attrs(cluster_id, token=None):
    cluster_attrs = {}

    REQ_SES = requests.Session()
    REQ_SES.trust_env = False

    if token is not None:
        REQ_SES.headers.update({'X-Auth-Token': token})

    URL = 'http://{0}:{1}/{2}'
    NAILGUN_API_URL = 'api/clusters/{0}'

    cluster_url = NAILGUN_API_URL.format(cluster_id)
    request_url = URL.format(cfg.CONF.adapter.nailgun_host,
                             cfg.CONF.adapter.nailgun_port,
                             cluster_url)

    response = REQ_SES.get(request_url).json()
    release_id = response.get('release_id', 'failed to get id')

    release_url = URL.format(
        cfg.CONF.adapter.nailgun_host, cfg.CONF.adapter.nailgun_port,
        'api/releases/{0}'.format(release_id))

    deployment_tags = set()

    fuel_version = response.get('fuel_version')
    if fuel_version:
        deployment_tags.add(fuel_version)

    release_data = REQ_SES.get(release_url).json()

    if 'version' in release_data:
        cluster_attrs['release_version'] = release_data['version']

    # info about deployment type and operating system
    mode = 'ha' if 'ha' in response['mode'].lower() else response['mode']
    deployment_tags.add(mode)
    deployment_tags.add(release_data.get(
        'operating_system', 'failed to get os'))

    # networks manager
    network_type = response.get('net_provider', 'nova_network')
    deployment_tags.add(network_type)

    # info about murano/sahara clients installation
    request_url += '/' + 'attributes'
    response = REQ_SES.get(request_url).json()

    public_assignment = response['editable'].get('public_network_assignment')
    if not public_assignment or \
            public_assignment['assign_to_all_nodes']['value']:
        deployment_tags.add('public_on_all_nodes')

    additional_components = \
        response['editable'].get('additional_components', dict())

    use_vcenter = response['editable']['common'].get('use_vcenter', None)
    libvrt_data = response['editable']['common'].get('libvirt_type', None)

    if use_vcenter:
        deployment_tags.add('use_vcenter')

    additional_depl_tags = set()

    comp_names = ['murano', 'sahara', 'heat', 'ceilometer']

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
    if libvrt_data and libvrt_data.get('value'):
        deployment_tags.add(libvrt_data['value'])

    cluster_attrs['deployment_tags'] = set(
        [tag.lower() for tag in deployment_tags]
    )

    return cluster_attrs


def _add_cluster_testing_pattern(session, cluster_data):
    to_database = []

    global TEST_REPOSITORY

    # populate cache if it's empty
    if not TEST_REPOSITORY:
        cache_test_repository(session)

    for test_set in TEST_REPOSITORY:
        if nose_utils.is_test_available(cluster_data, test_set):

            testing_pattern = {}
            testing_pattern['cluster_id'] = cluster_data['id']
            testing_pattern['test_set_id'] = test_set['test_set_id']
            testing_pattern['tests'] = []

            for test in test_set['tests']:
                if nose_utils.is_test_available(cluster_data, test):
                    testing_pattern['tests'].append(test['name'])

            to_database.append(
                models.ClusterTestingPattern(**testing_pattern)
            )

    session.add_all(to_database)
