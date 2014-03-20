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

import argparse
import sys


def parse_cli_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    cleandb_parser = subparsers.add_parser('cleandb')
    cleandb_parser.add_argument(
        '--dbpath',
        default='postgresql+psycopg2://ostf:ostf@localhost/ostf'
    )

    return parser.parse_args(sys.argv[1:])
