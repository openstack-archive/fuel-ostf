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
import sys

from oslo.config import cfg


adapter_group = cfg.OptGroup(name='adapter',
                             title='Adapter Options')

adapter_opts = [
    cfg.StrOpt('server_host',
               default='127.0.0.1',
               help="adapter host"),
    cfg.IntOpt('server_port',
               default=8777,
               help="Port number"),
    cfg.StrOpt('dbpath',
               default='postgresql+psycopg2://ostf:ostf@localhost/ostf',
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
               default='/var/log/ostf.log',
               help="")
]

cli_opts = [
    cfg.BoolOpt('debug', default=False),
    cfg.BoolOpt('after-initialization-environment-hook', default=False),
    cfg.StrOpt('debug_tests')
]


cfg.CONF.register_cli_opts(cli_opts)
cfg.CONF.register_opts(adapter_opts, group='adapter')


DEFAULT_CONFIG_DIR = os.path.join(os.path.abspath(
    os.path.dirname(__file__)), '/etc')

DEFAULT_CONFIG_FILE = "ostf.conf"


def init_config(args=[]):

    config_files = []

    failsafe_path = "/etc/ostf/" + DEFAULT_CONFIG_FILE

    # Environment variables override defaults...
    custom_config = os.environ.get('CUSTOM_OSTF_CONFIG')
    if custom_config:
        path = custom_config
    else:
        conf_dir = os.environ.get('OSTF_CONFIG_DIR',
                                  DEFAULT_CONFIG_DIR)
        conf_file = os.environ.get('OSTF_CONFIG', DEFAULT_CONFIG_FILE)

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

    cfg.CONF(args, project='ostf', default_config_files=config_files)
