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

from bottle import route, run


cluster_fixture = {
    1: {
        'cluster_meta': {
            'release_id': 1,
            'mode': 'ha'
        },
        'release_data': {
            'operating_system': 'rhel'
        },
        'cluster_attributes': {
            'editable': {
                'additional_components': {}
            }
        }
    },
    2: {
        'cluster_meta': {
            'release_id': 2,
            'mode': 'multinode',
        },
        'release_data': {
            'operating_system': 'ubuntu'
        },
        'cluster_attributes': {
            'editable': {
                'additional_components': {}
            }
        }
    },
    3: {
        'cluster_meta': {
            'release_id': 3,
            'mode': 'ha'
        },
        'release_data': {
            'operating_system': 'rhel'
        },
        'cluster_attributes': {
            'editable': {
                'additional_components': {
                    'murano': {
                        'value': True
                    },
                    'savanna': {
                        'value': False
                    }
                }
            }
        }
    },
    4: {
        'cluster_meta': {
            'release_id': 4,
            'mode': 'test_error'
        },
        'release_data': {
            'operating_system': 'none'
        },
        'cluster_attributes': {
            'editable': {
                'additional_components': {}
            }
        }
    },
    5: {
        'cluster_meta': {
            'release_id': 5,
            'mode': 'dependent_tests'
        },
        'release_data': {
            'operating_system': 'none'
        },
        'cluster_attributes': {
            'editable': {
                'additional_components': {}
            }
        }
    }
}


@route('/api/clusters/<id:int>')
def serve_cluster_meta(id):
    return cluster_fixture[id]['cluster_meta']


@route('/api/releases/<id:int>')
def serve_cluster_release_info(id):
    return cluster_fixture[id]['release_data']


@route('/api/clusters/<id:int>/attributes')
def serve_cluster_attributes(id):
    return cluster_fixture[id]['cluster_attributes']


run(host='localhost', port=8000, debug=True)
