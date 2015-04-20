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

USED_SPACE_LIMIT_PERCENTS = 90


class DiskSpaceTest(cloudvalidation.CloudValidationTest):
    """Cloud Validation Test class for disk space checks."""

    def _check_host_used_space(self, host):
        """Returns used disk space in percentage on host."""

        cmd = 'df --output=pcent | grep "[0-9]"'
        err_msg = "Cannot check free space on host {host}".format(host=host)

        out, err = self.verify(5, self._run_ssh_cmd, 1, err_msg,
                               'check free space on host', host, cmd)

        partitions = [float(percent[:-1]) for percent in out.split()]
        partitions = filter(lambda perc: perc >= USED_SPACE_LIMIT_PERCENTS,
                            partitions)
        return partitions

    def test_disk_space_outage(self):
        """Check disk space outage on controller and compute nodes
        Target component: Nova

        Scenario:
            1. Check outage on controller and compute nodes

        Duration: 20 s.

        Available since release: 2014.2-6.1
        """
        usages = filter(self._check_host_used_space,
                        self.computes + self.controllers)

        err_msg = "Nearly disk outage state detected on host(s): %s" % usages

        self.verify_response_true(not usages, err_msg, 1)
