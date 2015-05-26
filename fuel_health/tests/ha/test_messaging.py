# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2015 Mirantis, Inc.
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

import time
import threading
import uuid

from oslo.config import cfg
import oslo.messaging as oslo_messaging

from fuel_health import ha_base


class TestServerEndpoint(object):
    """This MessagingServer that will be used during functional testing."""

    def __init__(self):
        self.ival = 0
        self.sval = ''

    def add(self, ctxt, increment):
        self.ival += increment
        return self.ival

    def subtract(self, ctxt, increment):
        if self.ival < increment:
            raise ValueError("ival can't go negative!")
        self.ival -= increment
        return self.ival

    def append(self, ctxt, text):
        self.sval += text
        return self.sval


class RpcCall(object):
    def __init__(self, client, method, context):
        self.client = client
        self.method = method
        self.context = context

    def __call__(self, **kwargs):
        self.context['time'] = time.ctime()
        self.context['cast'] = False
        result = self.client.call(self.context, self.method, **kwargs)
        return result


class RpcCast(RpcCall):
    def __call__(self, **kwargs):
        self.context['time'] = time.ctime()
        self.context['cast'] = True
        self.client.cast(self.context, self.method, **kwargs)


class ClientStub(object):
    def __init__(self, transport, target, cast=False, name=None, **kwargs):
        self.name = name or "functional-tests"
        self.cast = cast
        self.client = oslo_messaging.RPCClient(transport, target, **kwargs)

    def __getattr__(self, name):
        context = {"application": self.name}
        if self.cast:
            return RpcCast(self.client, name, context)
        else:
            return RpcCall(self.client, name, context)


class SanityMessagingTest(ha_base.RabbitSanityClass):
    """Class contains tests that check basic messaging functionality.

    Special requirements:
        1. oslo.messaging should be installed.
    """
    def setUp(self):
        super(SanityMessagingTest, self).setUp()

        rabbit_pwd = self.get_conf_values().strip()
        self.url = "rabbit://nova:%s@%s:5673//" % (rabbit_pwd,
                                                   self._controllers[0])

        # create transport
        self.transport = oslo_messaging.get_transport(cfg.CONF, url=self.url)
        self.addCleanup(self.transport.cleanup)

        # create server
        self.target = oslo_messaging.Target(
            topic="topic_" + str(uuid.uuid4()),
            server="server_" + str(uuid.uuid4()))
        self.endpoint = TestServerEndpoint()
        self.server = oslo_messaging.get_rpc_server(
            self.transport, self.target, [self.endpoint])

        self.thread = threading.Thread(target=self.server.start)
        self.thread.daemon = True
        self.thread.start()
        # allow time for the server to connect to the broker
        time.sleep(0.5)

        self.addCleanup(self.thread.join)
        self.addCleanup(self.server.stop)

        self.client = ClientStub(self.transport, self.target,
                                 cast=False, timeout=5)

    def test_list_stacks(self):
        """Check, that RPC call() calls endpoint methods.
        Target component: oslo.messaging

        Scenario:
            1. Check, that RPC calls reach endpoint methods

        Duration: 5 s.
        """

        self.assertEqual(0, self.server.dispatcher.endpoints[0].ival)
        self.client.add(increment=1)

        def _assert():
            self.assertEqual(1, self.server.dispatcher.endpoints[0].ival)

        self.verify(
            secs=2,
            func=_assert,
            step=1,
            msg='Endpoint methods was not called.',
            action='RPC call()',
        )
