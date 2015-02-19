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

from fuel_health import cloudvalidation

LOG = logging.getLogger(__name__)


class LogRotationTest(cloudvalidation.CloudValidationTest):
    """TestClass contains log rotation test."""

    def test_logrotate(self):
        """Check log rotation configuration on all nodes
        Target component: Logging

        Scenario:
            1. Check logrotate cron job on all controller and compute nodes
        Duration: 20 s.

        Available since release: 2014.2-6.1
        """
        cmd = (
            "find /etc/crontab /etc/cron.daily /etc/cron.hourly "
            " /var/spool/cron/ -type f"
            " | xargs grep -qP '^[^#]*logrotate'"
        )

        fail_msg = 'Logrotate is not configured on node(s) %s'
        failed = set()
        for host in self.controllers + self.computes:
            try:
                self.verify(
                    5, self._run_ssh_cmd_with_exit_code,
                    1, fail_msg % host,
                    'checking logrotate', host, cmd)
            except AssertionError:
                failed.add(host)
        failed_hosts = ', '.join(failed)
        self.verify_response_true(len(failed) == 0, fail_msg % failed_hosts, 1)
