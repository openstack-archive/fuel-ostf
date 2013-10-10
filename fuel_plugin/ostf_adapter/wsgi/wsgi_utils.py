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

from fuel_plugin.ostf_adapter.storage import engine, models
from fuel_plugin.ostf_adapter.nose_plugin import nose_discovery


CORE_PATH = conf.debug_tests if conf.get('debug_tests') else 'fuel_health'


def discovery_check(cluster):
    #get needed information from nailgun via series of
    #requests to nailgun api. At this time we need
    #info about deployment type(ha, non-ha), type of network
    #management (nova-network, quntum) and attributes that
    #indicate that savanna/murano is installed
    cluster_deployment_args = _get_cluster_depl_tags(cluster)

    cluster_data = {
        'cluster_id': cluster,
        'deployment_tags': cluster_deployment_args
    }

    session = engine.get_session()
    with session.begin(subtransactions=True):
        test_sets = session.query(models.TestSet)\
            .filter_by(cluster_id=cluster)\
            .all()

        if not test_sets:
            nose_discovery.discovery(
                path=CORE_PATH,
                deployment_info=cluster_data
            )
        else:
            for testset in test_sets:
                deployment_tags = testset.deployment_tags
                deployment_tags = deployment_tags if deployment_tags else []
                if not set(deployment_tags).issubset(
                    cluster_data['deployment_tags']
                ):
                    #perform cascade deletion of testset
                    #and corresponding to it tests and
                    #testruns with their tests too
                    session.query(models.TestSet)\
                        .filter_by(id=testset.id)\
                        .filter_by(cluster_id=testset.cluster_id)\
                        .delete()

            #perform final discovery for tests
            nose_discovery.discovery(
                path=CORE_PATH,
                deployment_info=cluster_data
            )


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
    mode = 'ha' if 'ha' in response['mode'] else response['mode']
    deployment_tags.add(mode)
    deployment_tags.add(response['release']['operating_system'])

    #info about murano/savanna clients installation
    nailgun_url += '/' + 'attributes'
    response = req_ses.get(nailgun_url).json()

    additional_components = \
        response['editable']['additional_components']

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

    if additional_depl_tags:
        deployment_tags.add('additional_components')
        deployment_tags.update(additional_depl_tags)

    return deployment_tags
