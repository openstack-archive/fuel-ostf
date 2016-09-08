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

import logging

from fuel_health.common import ssh
from fuel_health import test


LOG = logging.getLogger(__name__)


class HAProxyCheck(test.BaseTestCase):
    """TestClass contains HAProxy checks."""
    @classmethod
    def setUpClass(cls):
        super(HAProxyCheck, cls).setUpClass()
        cls.controllers = cls.config.compute.online_controllers
        cls.controller_key = cls.config.compute.path_to_private_key
        cls.controller_user = cls.config.compute.ssh_user

    def setUp(self):
        super(HAProxyCheck, self).setUp()
        if not self.controllers:
            self.skipTest('There are no controller nodes')

    def _check_haproxy_backend(self, remote,
                               services=None, nodes=None,
                               ignore_services=None, ignore_nodes=None):
        """Check DOWN state of HAProxy backends. Define names of service or
        nodes if need check some specific service or node. Use ignore_services
        for ignore service status on all nodes. Use ignore_nodes for ignore all
        services on all nodes. Ignoring has a bigger priority.
        :param remote: SSHClient
        :param service: List
        :param nodes: List
        :param ignore_services: List
        :param ignore_nodes: List
        :return dict
        """
        cmd = 'haproxy-status.sh | egrep -v "BACKEND|FRONTEND"'

        pos_filter = (services, nodes)
        neg_filter = (ignore_services, ignore_nodes)
        grep = ['|egrep "{0}"'.format('|'.join(n)) for n in pos_filter if n]
        grep.extend(
            ['|egrep -v "{0}"'.format('|'.join(n)) for n in neg_filter if n])

        return remote.exec_command("{0}{1}".format(cmd, ''.join(grep)))

    def test_001_check_state_of_backends(self):
        """Check state of haproxy backends on controllers
        Target Service: HA haproxy

        Scenario:
            1. Ssh on each controller and get state of HAProxy backends
            2. Check backend state for availability
        Duration: 10 s.
        Available since release: 2015.1.0-8.0
        """
        LOG.info("Controllers nodes are %s" % self.controllers)
        for controller in self.controllers:
            remote = ssh.Client(controller, self.controller_user,
                                key_filename=self.controller_key,
                                timeout=100)
            ignore_services = []
            if 'neutron' not in self.config.network.network_provider:
                ignore_services.append('nova-metadata-api')
            haproxy_status = self.verify(
                10, self._check_haproxy_backend, 1,
                "Can't get state of backends.",
                "Getting state of backends",
                remote,
                ignore_services=ignore_services)

            dead_backends = filter(lambda x: 'DOWN' in x,
                                   haproxy_status.splitlines())
            backends_message = "Dead backends {0}"\
                .format(dead_backends)
            LOG.debug(backends_message)
            error_message = "Step 2 failed: " + backends_message
            self.verify_response_true(
                len(dead_backends) == 0, error_message)
