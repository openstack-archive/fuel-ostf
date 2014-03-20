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
import signal
from kombu import Consumer, Connection
from kombu.common import eventloop

from base_stuff import default_conn_string, ostf_queue
from fuel_plugin.ostf_adapter.orchestrator import callbacks

LOG = logging.getLogger(__name__)


def basic_consumer():
    LOG.info('Start consuming messages for orchestrator')
    #ignore signals from children
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)

    with Connection(default_conn_string) as conn:
        with Consumer(conn, queues=[ostf_queue],
                      callbacks=[callbacks.start_testruns_callback],
                      accept=['json']):

            #documentation says that eventloop is efficient wrapper
            #around drain_events method
            for _ in eventloop(conn, timeout=1, ignore_timeouts=True):
                pass
