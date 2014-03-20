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

from kombu import Producer, Connection
from base_stuff import default_conn_string, ostf_exchange

LOG = logging.getLogger(__name__)


def send_message(payload):
    LOG.info('Senging message with payload: {0}'.format(payload))
    with Connection(default_conn_string) as conn:
        producer = Producer(conn, exchange=ostf_exchange)
        LOG.info('#### before publishing')
        producer.publish(payload, serializer='json')
        LOG.info('#### after publishing')
