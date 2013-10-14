# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import time

import fuel_health.common.ssh

LOG = logging.getLogger(__name__)


class RabbitClient(object):
    def __init__(self, host, username, key, timeout,
                 rabbit_username='nova', rabbit_password=None):
        self.host = host
        self.username = username
        self.key_file = key
        self.timeout = timeout
        self.rabbit_user = rabbit_username
        self.rabbit_password = rabbit_password

        self.ssh = fuel_health.common.ssh.Client(
            host=self.host,
            username=self.username,
            key_filename=self.key_file,
            timeout=self.timeout)

    def list_nodes(self):
        output = self.ssh.exec_command('rabbitmqctl cluster_status')
        return output.split('\r\n')[1:-2]

    def list_queues(self):
        query = self._query('queues?"columns=name&sort=name"', header=False)
        return self._execute(query)

    def create_queue(self, queue_name):
        query = self._query(
            query='queues/%2f/{queue_name}'.format(queue_name=queue_name),
            type='-XPUT',
            arguments='-d \'{}\''
        )
        return self._execute(query)

    def delete_queue(self, queue_name):
        query = self._query(
            query='queues/%2f/{queue_name}'.format(queue_name=queue_name),
            type='-XDELETE'
        )
        return self._execute(query)

    def create_exchange(self, exchange_name):
        query = self._query(
            query='exchanges/%2f/{name}'.format(name=exchange_name),
            type='-XPUT',
            arguments='-d \'{"type":"direct"}\''
        )
        return self._execute(query)

    def delete_exchange(self, exchange_name):
        query = self._query(
            query='exchanges/%2f/{name}'.format(name=exchange_name),
            type='-XDELETE'
        )
        return self._execute(query)

    def create_binding(self, exchange_name, queue_name, binding_name):
        query = self._query(
            query='bindings/%2f/e/{ename}/q/{qname}/{name}'.format(
                ename=exchange_name,
                qname=queue_name,
                name=binding_name
            ),
            type='-XPUT'
        )
        return self._execute(query)

    def delete_binding(self, exchange_name, queue_name, binding_name):
        query = self._query(
            query='bindings/%2f/e/{ename}/q/{qname}/{name}'.format(
                ename=exchange_name,
                qname=queue_name,
                name=binding_name
            ),
            type='-XDELETE'
        )
        return self._execute(query)

    def publish_message(self, message, exchange, binding):
        query = self._query(
            query='exchanges/%2f/{ename}/publish'.format(ename=exchange),
            type='-XPOST',
            arguments='-d \'{{"properties":{{}},"routing_key":"{bname}",'
                      '"payload":"{msg}","payload_encoding":"string"}}\''.
            format(
                bname=binding,
                msg=message
            )
        )
        return self._execute(query)

    def get_message(self, queue):
        query = self._query(
            query='queues/%2f/{qname}/get'.format(qname=queue),
            type='-XPOST',
            arguments='-d \'{"count":1,"requeue":false,"encoding":"auto"}\''
        )
        return self._execute(query)

    def _query(self, query, header=True, type='-XGET', arguments=''):
        start = (header and 'curl -i') or 'curl'
        return '{start} -u {ruser}:{rpass} -H "content-type:application/json"'\
               ' {type} {args} http://localhost:55672/api/{query}'.\
            format(
                start=start,
                ruser=self.rabbit_user,
                rpass=self.rabbit_password,
                type=type, query=query,
                args=arguments
            )

    def _execute(self, query, times=5):
        exception = None
        for i in range(times + 1):
            try:
                result = self.ssh.exec_command(query)
                if result:
                    return result
                time.sleep(1)
            except Exception as exc:
                exception = exc
                LOG.debug(exc)
        raise exception
