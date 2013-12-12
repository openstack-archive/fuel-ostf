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

import signal
import subprocess
import time


def setup():
    global processes_pool

    with open('fuel_plugin/testing/tests/etc/server.log', 'w') as serverlogs:
        with open('/dev/null', 'w') as devnull:
            processes_pool = tuple(
                [
                    subprocess.Popen(
                        [
                            'python',
                            'fuel_plugin/testing/test_utils/nailgun_mimic.py'
                        ],
                        stdout=devnull,
                        stderr=devnull
                    ),
                    subprocess.Popen(
                        [
                            'ostf-server',
                            '--debug',
                            '--nailgun-port=8888',
                            ('--debug_tests=fuel_plugin/testing/'
                             'fixture/dummy_tests')
                        ],
                        stdout=serverlogs,
                        stderr=serverlogs
                    )
                ]
            )
    time.sleep(5)


def teardown():
    for process in processes_pool:
        process.send_signal(signal.SIGINT)
        process.wait()
