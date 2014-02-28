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

import pecan
from fuel_plugin.ostf_adapter.wsgi import hooks


PECAN_DEFAULT = {
    'server': {
        'host': '0.0.0.0',
        'port': 8989
    },
    'app': {
        'root': 'fuel_plugin.ostf_adapter.wsgi.root.RootController',
        'modules': ['fuel_plugin.ostf_adapter.wsgi']
    },
    'nailgun': {
        'host': '127.0.0.1',
        'port': 8000
    },
    'dbpath': 'postgresql+psycopg2://ostf:ostf@localhost/ostf',
    'debug': False,
    'debug_tests': 'fuel_plugin/tests/functional/dummy_tests'
}


def setup_config(custom_pecan_config):
    '''
    Updates defaults values for pecan server
    by those supplied via command line arguments
    when ostf-server is started
    '''
    config_to_use = PECAN_DEFAULT
    config_to_use.update(custom_pecan_config)
    pecan.conf.update(config_to_use)


def setup_app(config=None):
    setup_config(config or {})
    app = pecan.make_app(
        pecan.conf.app.root,
        debug=pecan.conf.debug,
        force_canonical=True,
        hooks=[hooks.CustomTransactionalHook(dbpath=pecan.conf.dbpath)]
    )
    return app
