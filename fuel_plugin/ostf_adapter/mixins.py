#    Copyright 2015 Mirantis, Inc.
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

try:
    from oslo.config import cfg
except ImportError:
    from oslo_config import cfg

try:
    from oslo.serialization import jsonutils
except ImportError:
    from oslo_serialization import jsonutils

import requests
from sqlalchemy.orm import joinedload

from fuel_plugin.ostf_adapter.nose_plugin import nose_utils
from fuel_plugin.ostf_adapter.storage import models

LOG = logging.getLogger(__name__)

TEST_REPOSITORY = []
# TODO(ikutukov): remove hardcoded Nailgun API urls here and below
NAILGUN_VERSION_API_URL = 'http://{0}:{1}/api/v1/version'


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


def get_version_string(token=None):
    requests_session = requests.Session()
    requests_session.trust_env = False
    request_url = NAILGUN_VERSION_API_URL.format(cfg.CONF.adapter.nailgun_host,
                                                 cfg.CONF.adapter.nailgun_port)
    try:
        response = requests_session.get(request_url).json()
        return jsonutils.dumps(response)
    except (ValueError, IOError, requests.exceptions.HTTPError):
        return "Can't obtain version via Nailgun API"


def _get_cluster_attrs(cluster_id, token=None):
    cluster_attrs = {}

    REQ_SES = requests.Session()
    REQ_SES.trust_env = False
    REQ_SES.verify = False

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

    nodes_url = URL.format(
        cfg.CONF.adapter.nailgun_host, cfg.CONF.adapter.nailgun_port,
        'api/nodes?cluster_id={0}'.format(cluster_id))
    nodes_response = REQ_SES.get(nodes_url).json()
    if 'objects' in nodes_response:
        nodes_response = nodes_response['objects']
    enable_without_ceph = filter(lambda node: 'ceph-osd' in node['roles'],
                                 nodes_response)

    sriov_compute_ids = []
    dpdk_compute_ids = []  # Check env has computes with DPDK
    compute_ids = [node['id'] for node in nodes_response
                   if "compute" in node['roles']]
    for compute_id in compute_ids:
        ifaces_url = URL.format(
            cfg.CONF.adapter.nailgun_host, cfg.CONF.adapter.nailgun_port,
            'api/nodes/{id}/interfaces'.format(id=compute_id))
        ifaces_resp = REQ_SES.get(ifaces_url).json()
        for iface in ifaces_resp:
            if 'interface_properties' in iface:
                if ('sriov' in iface['interface_properties'] and
                        iface['interface_properties']['sriov']['enabled']):
                    sriov_compute_ids.append(compute_id)
                if 'dpdk' in iface['interface_properties']:
                    if 'enabled' in iface['interface_properties']['dpdk']:
                        if iface['interface_properties']['dpdk']['enabled']:
                            dpdk_compute_ids.append(compute_id)
            else:
                if ('sriov' in iface['attributes'] and
                        iface['attributes']['sriov']['enabled']['value']):
                    sriov_compute_ids.append(compute_id)
                if 'dpdk' in iface['attributes']:
                    if 'enabled' in iface['attributes']['dpdk']:
                        if iface['attributes']['dpdk']['enabled']['value']:
                            dpdk_compute_ids.append(compute_id)

    deployment_tags = set()

    if sriov_compute_ids:
        deployment_tags.add('sriov')

    if dpdk_compute_ids:
        deployment_tags.add('computes_with_dpdk')
    if not dpdk_compute_ids or set(compute_ids) - set(dpdk_compute_ids):
        deployment_tags.add('computes_without_dpdk')

    if not enable_without_ceph:
        deployment_tags.add('enable_without_ceph')

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

    libvrt_data = response['editable']['common'].get('libvirt_type', None)

    additional_depl_tags = set()

    comp_names = ['murano', 'sahara', 'heat', 'ironic']

    def processor(comp):
        if comp in comp_names:
            if additional_components.get(comp)\
               and additional_components.get(comp)['value']\
               is True:
                additional_depl_tags.add(comp)

    for comp in comp_names:
        processor(comp)

    # TODO(freerunner): Rework murano part after removal murano from the box
    murano_settings = response['editable'].get('murano_settings', {})
    # murano_glance_artifacts_plugin was moved from additional components
    # in mitaka, thus for old environments it should taken from them
    murano_glance_artifacts_plugin = murano_settings.get(
        'murano_glance_artifacts_plugin',
        additional_components.get('murano_glance_artifacts_plugin')
    )
    # NOTE(freerunner): Murano settings appears only if murano enabled
    murano_artifacts = None
    if murano_glance_artifacts_plugin:
        murano_artifacts = murano_glance_artifacts_plugin['value']

    detach_murano = response['editable'].get('detach-murano', None)
    murano_plugin_enabled = None
    if detach_murano:
        murano_plugin_enabled = detach_murano['metadata'].get('enabled', None)
        if murano_plugin_enabled:
            additional_depl_tags.add('murano_plugin')

    # TODO(freerunner): Rework GLARE discover mechanism after
    # TODO(freerunner): removal murano from the box
    if murano_artifacts:
        additional_depl_tags.add('murano_use_glare')
    # NOTE(freerunner): Murano plugin will always support only one version
    elif detach_murano and murano_plugin_enabled and (
            detach_murano['metadata']['versions'][0]
            ['murano_glance_artifacts'].get('value', None)):
        additional_depl_tags.add('murano_use_glare')
    # NOTE(freerunner): Set this tag only if murano is present
    elif murano_plugin_enabled or murano_settings:
        additional_depl_tags.add('murano_without_glare')

    storage_components = response['editable'].get('storage', dict())

    storage_comp = ['volumes_ceph', 'images_ceph', 'ephemeral_ceph',
                    'objects_ceph', 'osd_pool_size', 'volumes_lvm']

    storage_depl_tags = set()

    def storage_processor(scomp):
        if scomp in storage_comp:
            if storage_components.get(scomp) \
                    and storage_components.get(scomp)['value'] \
                    is True:
                storage_depl_tags.add(scomp)
    for scomp in storage_comp:
        storage_processor(scomp)

    if additional_depl_tags:
        deployment_tags.add('additional_components')
        deployment_tags.update(additional_depl_tags)
    if storage_depl_tags:
        deployment_tags.add('storage')
        deployment_tags.update(storage_depl_tags)
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
