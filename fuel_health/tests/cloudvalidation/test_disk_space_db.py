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

from fuel_health import cloudvalidation


class DBSpaceTest(cloudvalidation.CloudValidationTest):
    """Cloud Validation Test class for free space for DB."""

    def _check_db_disk_expectation_warning(self, host):
        """Checks whether DB expects less free space than actually
        is presented on the controller node
        """
        scheduler_log = 'nova-scheduler.log'

        if self.config.compute.deployment_os.lower() == 'centos':
            scheduler_log = 'scheduler.log'

        err_msg = "Cannot check {scheduler_log} at {host}".format(
            host=host, scheduler_log=scheduler_log)

        warning_msg = "Host has more disk space than database expected"
        cmd = "fgrep '{msg}' -q /var/log/nova/{scheduler_log}".format(
            msg=warning_msg, scheduler_log=scheduler_log)

        out, err = self.verify(5, self._run_ssh_cmd, 1, err_msg,
                               'check nova-scheduler.log', host, cmd)

        self.verify_response_true(not err, err_msg, 1)

        return out

    def test_db_expectation_free_space(self):
        """Check disk space allocation for databases on controller nodes
        Target component: Nova

        Scenario:
            1. Check disk space allocation for databases on controller nodes

        Duration: 20 s.

        Deployment tags: disabled

        Available since release: 2014.2-6.1
        """

        hosts = filter(self._check_db_disk_expectation_warning,
                       self.controllers)

        self.verify_response_true(not hosts,
                                  ("Free disk space cannot be used "
                                   "by database on node(s): {hosts}"
                                   ).format(hosts=hosts),
                                  1)
