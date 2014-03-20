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

from kombu import Consumer, Connection

from base_stuff import default_conn_string, ostf_queue
from callbacks import simple_callback


def main():
    with Connection(default_conn_string) as conn:
        print('##### in main function')
        with Consumer(conn, queues=[ostf_queue], callbacks=[simple_callback],
                      accept=['json']):
            while True:
                try:
                    print('##### drain events')
                    conn.drain_events()
                except Exception as e:
                    print('#### exception ---> {0}'.format(e.message))
                    pass
                except KeyboardInterrupt:
                    print('##### exiting')
                    break


if __name__ == '__main__':
    main()
