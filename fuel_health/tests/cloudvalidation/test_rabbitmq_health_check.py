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
import re

from fuel_health import cloudvalidation

LOG = logging.getLogger(__name__)


class RabbitMQHealthTest(cloudvalidation.CloudValidationTest):
    """TestClass contains health tests for RabbitMQ."""

    RE_FILE_DESCRIPTORS = re.compile(
        '{total_limit,([0-9]+)},\s+{total_used,([0-9]+)}',
        re.M)

    RE_SOCKET_DESCRIPTORS = re.compile(
        '{sockets_limit,([0-9]+)},\s+{sockets_used,([0-9]+)}',
        re.M)

    RE_PROCESS_DESCRIPTORS = re.compile(
        '{processes,\[{limit,([0-9]+)},{used,([0-9]+)}\]}')

    FILE_DESCRIPTORS_LIMIT = 0.9
    SOCKET_DESCRIPTORS_LIMIT = 0.9
    PROCESS_DESCRIPTORS_LIMIT = 0.9

    def _check_opened_file_descriptors(self, host):
        """Check RabbitMQ for opened file descriptors excess on the host."""

        cmd = ('rabbitmqctl -q status | '
               'grep -Pzo "{file_descriptors,\s*(\[[^\[]+\])},"')

        out, err = self.verify(5, self._run_ssh_cmd, 1,
                               'Cannot check RabbitMQ status at %s' % host,
                               'check opened file descriptors',
                               host, cmd)

        try:
            matches = re.search(self.RE_FILE_DESCRIPTORS, out)
            limit, used = matches.groups()
            LOG.debug(('File descriptors: limit={limit}, used={used}'
                       ).format(limit=limit, used=used))

            return float(used)/float(limit) > self.FILE_DESCRIPTORS_LIMIT

        except (IndexError, AttributeError) as e:
            LOG.debug('An error occured: %s' % e.message)
            return False

    def _check_opened_socket_descriptors(self, host):
        """Check RabbitMQ for opened socket descriptors excess on the host."""

        cmd = ('rabbitmqctl -q status | '
               'grep -Pzo "{file_descriptors,\s*(\[[^\[]+\])},"')

        LOG.debug('Check host %s opened socket descriptors.' % host)

        out, err = self.verify(5, self._run_ssh_cmd, 1,
                               'Cannot check RabbitMQ status at %s' % host,
                               'check opened socket descriptors',
                               host, cmd)

        try:
            matches = re.search(self.RE_SOCKET_DESCRIPTORS, out)
            limit, used = matches.groups()
            LOG.debug(('Socket descriptors: limit={limit}, used={used}'
                       ).format(limit=limit, used=used))

            return float(used)/float(limit) > self.SOCKET_DESCRIPTORS_LIMIT

        except (IndexError, AttributeError) as e:
            LOG.debug('An error occured: %s' % e.message)
            return False

    def _check_erlang_process_descriptors(self, host):
        """Check RabbitMQ for Erlang processes excess on the host."""

        cmd = ('rabbitmqctl -q status | '
               'grep -Pzo "{processes,\[{limit,([0-9]+)},{used,([0-9]+)}\]}"')

        LOG.debug('Check host %s Erlang processes.' % host)

        out, err = self.verify(5, self._run_ssh_cmd, 1,
                               'Cannot check RabbitMQ status at %s' % host,
                               'check Erlang processes status',
                               host, cmd)

        try:
            matches = re.search(self.RE_PROCESS_DESCRIPTORS, out)
            limit, used = matches.groups()
            LOG.debug(('Process descirptors: limit={limit}, used={used}'
                       ).format(limit=limit, used=used))

            return float(used)/float(limit) > self.PROCESS_DESCRIPTORS_LIMIT

        except (IndexError, AttributeError) as e:
            LOG.debug('An error occured: %s' % e.message)
            return False

    def test_rabbitmq_opened_file_descriptors_excess(self):
        """Check opened file descriptors excess in RabbitMQ
        Target component: RabbitMQ

        Scenario:
            1. Check opened file descriptors excess in RabbitMQ
        Duration: 20 s.

        Available since release: 2015.1.0-7.0
        """

        hosts = filter(self._check_opened_file_descriptors, self.controllers)
        failed_hosts = ', '.join(hosts)[:-2]

        err_msg = 'An excess of opened file descriptors found at hosts: %s'

        self.verify_response_true(not hosts,
                                  err_msg % failed_hosts,
                                  1)

    def test_rabbitmq_opened_socket_descriptors_excess(self):
        """Check opened socket descriptors excess in RabbitMQ
        Target component: RabbitMQ

        Scenario:
            1. Check opened socket descriptors excess in RabbitMQ
        Duration: 20 s.

        Available since release: 2015.1.0-7.0
        """

        hosts = filter(self._check_opened_socket_descriptors, self.controllers)
        failed_hosts = ', '.join(hosts)[:-2]
        err_msg = 'An excess of opened socket descriptors found at hosts: %s'

        self.verify_response_true(not hosts,
                                  err_msg % failed_hosts,
                                  1)

    def test_rabbitmq_erlang_process_excess(self):
        """Check Erlang processes excess in RabbitMQ
        Target component: RabbitMQ

        Scenario:
            1. Check Erlang processes excess in RabbitMQ
        Duration: 20 s.

        Available since release: 2015.1.0-7.0
        """

        hosts = filter(self._check_erlang_process_descriptors,
                       self.controllers)
        failed_hosts = ', '.join(hosts)[:-2]

        err_msg = 'An excess of Erlang processes found at hosts: %s'

        self.verify_response_true(not hosts,
                                  err_msg % failed_hosts,
                                  1)
