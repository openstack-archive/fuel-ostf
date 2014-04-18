#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import os
import logging
import signal
import sys
import pecan
from gevent import pywsgi

from oslo.config import cfg

from fuel_plugin.ostf_adapter import cli_config
from fuel_plugin.ostf_adapter import nailgun_hooks
from fuel_plugin.ostf_adapter import logger
from fuel_plugin.ostf_adapter.wsgi import app
from fuel_plugin.ostf_adapter.nose_plugin import nose_discovery
from fuel_plugin.ostf_adapter.storage import engine
from fuel_plugin.ostf_adapter import mixins

adapter_group = cfg.OptGroup(name='adapter',
                             title='Adapter Options')
AdapterGroup = [
    cfg.StrOpt('server_host',
               default='127.0.0.1',
               help="adapter host"),
    cfg.StrOpt('server_port',
               default='8777',
               help="Port number"),
    cfg.StrOpt('dbpath',
               default='postgresql+psycopg2://ostf:ostf@localhost/ostf',
               help=""),
    cfg.BoolOpt('debug',
                default=True,
                help=""),
    cfg.StrOpt('debug_tests',
               default='default',
               help=""),
    cfg.StrOpt('lock_dir',
               default='/var/lock',
               help=""),
    cfg.StrOpt('nailgun_host',
               default='127.0.0.1',
               help=""),
    cfg.StrOpt('nailgun_port',
               default='8000',
               help=""),
    cfg.StrOpt('log_file',
               default='/var/log/ostf-stdout.log',
               help=""),
    cfg.BoolOpt('after_init_hook',
                default='False',
                help='Should be true when we need migrate data to db')
    ]


def register_adapter_opts(conf):
    conf.register_group(adapter_group)
    for opt in AdapterGroup:
        conf.register_opt(opt, group='adapter')


def process_singleton(cls):
    """Wrapper for classes... To be instantiated only one time per process"""
    instances = {}

    def wrapper(*args, **kwargs):
        pid = os.getpid()
        if pid not in instances:
            instances[pid] = cls(*args, **kwargs)
        return instances[pid]

    return wrapper


@process_singleton
class Ostf_Config(object):

    DEFAULT_CONFIG_DIR = os.path.join(os.path.abspath(
        os.path.dirname(__file__)), '/etc')

    DEFAULT_CONFIG_FILE = "ostf.conf"

    def __init__(self):
        """Initialize a configuration from a conf directory and conf file."""
        config_files = []

        failsafe_path = "/etc/ostf/" + self.DEFAULT_CONFIG_FILE

        # Environment variables override defaults...
        custom_config = os.environ.get('CUSTOM_OSTF_CONFIG')
        if custom_config:
            path = custom_config
        else:
            conf_dir = os.environ.get('OSTF_CONFIG_DIR',
                                      self.DEFAULT_CONFIG_DIR)
            conf_file = os.environ.get('OSTF_CONFIG', self.DEFAULT_CONFIG_FILE)

            path = os.path.join(conf_dir, conf_file)

            if not (os.path.isfile(path)
                    or 'OSTF_CONFIG_DIR' in os.environ
                    or 'OSTF_CONFIG' in os.environ):
                path = failsafe_path

        if not os.path.exists(path):
            msg = "Config file %(path)s not found" % locals()
            print >> sys.stderr, RuntimeError(msg)
        else:
            config_files.append(path)

        cfg.CONF([], project='ostf', default_config_files=config_files)

        register_adapter_opts(cfg.CONF)
        self.adapter = cfg.CONF.adapter


class ConfigGroup(object):
    # USE SLOTS

    def __init__(self, opts):
        self.parse_opts(opts)

    def parse_opts(self, opts):
        for opt in opts:
            name = opt.name
            self.__dict__[name] = opt.default

    def __setattr__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem(self, key, value):
        self.__dict__[key] = value

    def __repr__(self):
        return u"{0} WITH {1}".format(
            self.__class__.__name__,
            self.__dict__)


def main():

    settings = Ostf_Config()

    cli_args = cli_config.parse_cli()

    config = {
        'server': {
            'host': settings.adapter.server_host or cli_args.host,
            'port': settings.adapter.server_port or cli_args.port
        },
        'dbpath': settings.adapter.dbpath or cli_args.dbpath,
        'debug': settings.adapter.debug or cli_args.debug,
        'debug_tests': settings.adapter.debug_tests or cli_args.debug_tests,
        'lock_dir': settings.adapter.lock_dir or cli_args.lock_dir,
        'nailgun': {
            'host': settings.adapter.nailgun_host or cli_args.nailgun_host,
            'port': settings.adapter.nailgun_port or cli_args.nailgun_port
        }
    }
    print config
    logger.setup(log_file=(
        settings.adapter.log_file or cli_args.log_file))

    log = logging.getLogger(__name__)

    root = app.setup_app(config=config)

    if getattr(cli_args, 'after_init_hook'):
        return nailgun_hooks.after_initialization_environment_hook()

    if settings.adapter.after_init_hook:
        return nailgun_hooks.after_initialization_environment_hook()

    with engine.contexted_session(pecan.conf.dbpath) as session:
        # performing cleaning of expired data (if any) in db
        mixins.clean_db(session)

        # discover testsets and their tests
        CORE_PATH = pecan.conf.debug_tests if \
            pecan.conf.get('debug_tests') else 'fuel_health'

        nose_discovery.discovery(path=CORE_PATH, session=session)

        # cache needed data from test repository
        mixins.cache_test_repository(session)

    host, port = pecan.conf.server.host, pecan.conf.server.port
    srv = pywsgi.WSGIServer((host, int(port)), root)

    log.info('Starting server in PID %s', os.getpid())
    log.info("serving on http://%s:%s", host, port)

    try:
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
