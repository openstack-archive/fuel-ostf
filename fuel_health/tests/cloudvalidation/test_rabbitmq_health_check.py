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
import re

from fuel_health import ha_base

LOG = logging.getLogger(__name__)


class RabbitCloudvalidationTest(ha_base.RabbitSanityClass):
    """TestClass contains health tests for RabbitMQ."""

    def _get_rabbit_status(self, host):
        LOG.info('Check RabbitMQ status')

        remote = self.get_ssh_connection_to_controller(host)
        cmd = 'rabbitmqctl -q status'
        stdout = self.verify(
            120, remote.exec_command, 1,
            'Cannot check RabbitMQ status at %s' % host,
            'check RabbitMQ status',
            cmd)
        try:
            re_status = re.compile(('file_descriptors,\s*\['
                                    '{total_limit,([0-9]+)},\s*'
                                    '{total_used,([0-9]+)},\s*'
                                    '{sockets_limit,([0-9]+)},\s*'
                                    '{sockets_used,([0-9]+)}\]},\s*'
                                    '{processes,\[{limit,([0-9]+)},'
                                    '{used,([0-9]+)'))

            params = re_status.search(stdout).groups()

            return {'opened file descriptors': {'limit': params[0],
                                                'used': params[1]},
                    'opened socket descriptors': {'limit': params[2],
                                                  'used': params[3]},
                    'Erlang processes': {'limit': params[4],
                                         'used': params[5]}}

        except AttributeError as e:
            LOG.error('An error occured: {msg}'.format(msg=e.message))
            self.fail('Cannot check RabbitMQ at "{host}"'.format(
                      host=host))

    def _check_param_excess_limit(self, host, param,
                                  limit, used, limit_of_excess):
        """Check RabbitMQ status parameter excess."""

        LOG.debug('Check {param}: limit={limit}, used={used}'.format(
            param=param,
            limit=limit,
            used=used))

        return float(used)/float(limit) > limit_of_excess

    def test_rabbitmq_parameters_excess(self):
        """Check parameters excess in RabbitMQ.
        Target component: RabbitMQ

        Scenario:
            1. Check total opened file descriptors excess in RabbitMQ
            2. Check opened socket descriptors excess in RabbitMQ
            3. Check Erlang processes excess in RabbitMQ
        Duration: 45 s.

        Available since release: 2015.1.0-8.0
        """

        statuses = {}
        err_msg = 'An excess of {param} found at hosts: {hosts}'
        params = [{'name': 'opened file descriptors', 'limit': 0.9},
                  {'name': 'opened socket descriptors', 'limit': 0.9},
                  {'name': 'Erlang processes', 'limit': 0.9}]

        for host in self.amqp_hosts_name:
            statuses[host] = self._get_rabbit_status(host)

        for param in params:
            failed_hosts = []
            for host in statuses:
                name = param['name']
                if self._check_param_excess_limit(
                        host=host, param=name,
                        limit=statuses[host][name]['limit'],
                        used=statuses[host][name]['used'],
                        limit_of_excess=statuses[host][name]['limit']):

                    failed_hosts.append(host)

            self.verify_response_true(not failed_hosts,
                                      err_msg.format(
                                          param=param,
                                          hosts=', '.join(failed_hosts)),
                                      1)
