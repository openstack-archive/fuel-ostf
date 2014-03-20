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

from kombu import Producer, Connection
from base_stuff import default_conn_string, ostf_exchange


def main(message):
    with Connection(default_conn_string) as conn:
        producer = Producer(conn, exchange=ostf_exchange)

        print('#### publish message --> {0}'.format(message))
        producer.publish(message, serializer='json')


if __name__ == '__main__':
    message = {
        'name': 'James',
        'surname': 'Bond'
    }

    main(message)
