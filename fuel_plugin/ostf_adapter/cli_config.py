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

import argparse
import sys


def parse_cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('--after-initialization-environment-hook',
                        action='store_true', dest='after_init_hook')
    parser.add_argument('--debug',
                        action='store_true', dest='debug')
    parser.add_argument(
        '--dbpath', metavar='DB_PATH',
        default='postgresql+psycopg2://adapter:demo@localhost/testing_adapter')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', default='8989')
    parser.add_argument('--log_file', default=None, metavar='PATH')
    parser.add_argument('--nailgun-host', default='127.0.0.1')
    parser.add_argument('--nailgun-port', default='3232')
    parser.add_argument('--debug_tests', default=None)
    return parser.parse_args(sys.argv[1:])
