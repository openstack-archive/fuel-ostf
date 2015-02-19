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

USED_SPACE_LIMIT_PERCENTS = 90


class DiskSpaceTest(cloudvalidation.CloudValidationTest):
    """Cloud Validation Test class for disk space checks."""

    def _check_host_used_space(self, host):
        """Returns used disk space in percentage on host."""

        cmd = 'df'  # root file system
        err_msg = "Cannot check free space on host %s"

        out, err = self.verify(5, self._run_ssh_cmd, 1,
                               err_msg % host,
                               'check free space on host', host, cmd)

        for m_point in out.split('\n')[1:]:

            pc = [x for x in m_point.split(' ') if x.find('%') != -1]

            if pc and float(pc[0][:-1]) >= USED_SPACE_LIMIT_PERCENTS:
                return True  # outage detected

        return False

    def test_disk_space_outage(self):
        """Check: disk space outage on controller and compute nodes
        Target component: Nova

        Scenario:
            1. Check outage on controller and compute nodes

        Duration: 20 s.
        """
        usages = list()

        for host in self.computes + self.controllers:
            if self._check_host_used_space(host):
                usages.append(host)

        err_msg = "Nearly disk outage state detected on host(s): %s" % usages

        self.verify_response_true(not len(usages), err_msg, 1)
