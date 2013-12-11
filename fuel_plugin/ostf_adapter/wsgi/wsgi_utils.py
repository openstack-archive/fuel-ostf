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

from fuel_plugin.ostf_adapter.storage import models
from fuel_plugin.ostf_adapter \
    .storage.storage_utils import add_cluster_testing_pattern


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
            add_cluster_testing_pattern(session, cluster_data)

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
            add_cluster_testing_pattern(session, cluster_data)

            cluster_state.deployment_tags = \
                list(cluster_data['deployment_tags'])

            session.merge(cluster_state)


def _get_cluster_depl_tags(cluster_id):
    nailgun_api_url = 'api/clusters/{0}'.format(cluster_id)

    deployment_tags = set()
    nailgun_url = 'http://{0}:{1}/{2}'.format(
        conf.nailgun.host,
        conf.nailgun.port,
        nailgun_api_url
    )

    req_ses = requests.Session()
    req_ses.trust_env = False

    response = req_ses.get(nailgun_url).json()

    #info about deployment type and operating system
    mode = 'ha' if 'ha' in response['mode'].lower() else response['mode']
    deployment_tags.add(mode)
    deployment_tags.add(response['release']['operating_system'])

    #networks manager
    network_type = response.get('net_provider', 'nova_network')
    deployment_tags.add(network_type)

    #info about murano/savanna clients installation
    nailgun_url += '/' + 'attributes'
    response = req_ses.get(nailgun_url).json()

    additional_components = \
        response['editable'].get('additional_components', dict())

    additional_depl_tags = set()

    if additional_components.get('murano')\
       and additional_components.get('murano')['value'] is True:
        additional_depl_tags.add('murano')

    if additional_components.get('savanna')\
       and additional_components.get('savanna')['value'] is True:
        additional_depl_tags.add('savanna')

    if additional_components.get('heat')\
       and additional_components.get('heat')['value'] is True:
        additional_depl_tags.add('heat')

    if additional_components.get('ceilometer') \
        and additional_components.get('ceilometer')['value'] is True:
        additional_depl_tags.add('ceilometer')

    if additional_depl_tags:
        deployment_tags.add('additional_components')
        deployment_tags.update(additional_depl_tags)

    return set([tag.lower() for tag in deployment_tags])
