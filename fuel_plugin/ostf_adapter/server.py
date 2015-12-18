#    Copyright 2014 Mirantis, Inc.
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
import os
import signal
import sys

from gevent import pywsgi
try:
    from oslo.config import cfg
except ImportError:
    from oslo_config import cfg

from fuel_plugin.ostf_adapter import config as ostf_config
from fuel_plugin.ostf_adapter import logger
from fuel_plugin.ostf_adapter import mixins
from fuel_plugin.ostf_adapter import nailgun_hooks
from fuel_plugin.ostf_adapter.nose_plugin import nose_discovery
from fuel_plugin.ostf_adapter.storage import engine
from fuel_plugin.ostf_adapter.wsgi import app


CONF = cfg.CONF


def main():

    ostf_config.init_config(sys.argv[1:])

    logger.setup(log_file=CONF.adapter.log_file)

    log = logging.getLogger(__name__)
    log.info('Start app configuration')

    root = app.setup_app({})

    # completely clean db (drop tables, constraints and types)
    # plus drop alembic_version table (needed if, for example, head migration
    # script was changed after applying)
    if CONF.clear_db:
        return nailgun_hooks.clear_db(CONF.adapter.dbpath)

    if CONF.after_initialization_environment_hook:
        return nailgun_hooks.after_initialization_environment_hook()

    with engine.contexted_session(CONF.adapter.dbpath) as session:
        # performing cleaning of expired data (if any) in db
        mixins.delete_db_data(session)
        log.info('Cleaned up database.')
        # discover testsets and their tests
        core_path = CONF.debug_tests or 'fuel_health'

        log.info('Performing nose discovery with {0}.'.format(core_path))

        nose_discovery.discovery(path=core_path, session=session)

        # cache needed data from test repository
        mixins.cache_test_repository(session)

    log.info('Discovery is completed')
    host, port = CONF.adapter.server_host, CONF.adapter.server_port
    srv = pywsgi.WSGIServer((host, port), root)

    log.info('Starting server in PID %s', os.getpid())
    log.info("serving on http://%s:%s", host, port)

    try:
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
