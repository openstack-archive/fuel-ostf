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


class NTPTest(cloudvalidation.CloudValidationTest):
    """Cloud Validation Test class for NTP."""

    def _verify_ntp_config(self, host, step):
        """Checks if there's at least one time server in ntp.conf."""

        err_msg = 'There is no time servers in ntp.conf at {host}'.format(
                  host=host)

        cmd = 'grep "^\s*server" /etc/ntp.conf'
        err_grep_msg = 'Cannot read ntp.conf at {host}'.format(host=host)

        out, err = self.verify(5,
                               self._run_ssh_cmd,
                               step,
                               err_grep_msg,
                               'check ntp.conf',
                               host,
                               cmd)
        LOG.debug('OUT: '+out)
        result = bool(out)

        self.verify_response_true(result, err_msg, step)

    def _check_ntp(self, host, step, kind="unknown"):
        """Checks NTP on host."""

        self._verify_ntp_config(host, step)

        err_msg = 'An error occured while checking NTP at {host}'.format(
                  host=host)

        cmd = "ip netns exec vrouter ntpq -np"
        out, err = self.verify(5,
                               self._run_ssh_cmd,
                               step,
                               err_msg,
                               'check NTP',
                               host,
                               cmd)

        if u'Cannot open network namespace' in err:

            cmd = "ntpq -np"
            out, err = self.verify(5,
                                   self._run_ssh_cmd,
                                   step,
                                   err_msg,
                                   'check NTP',
                                   host,
                                   cmd)

            checks = [(u'Connection refused',
                       u'No connection to server at {host}'.format(host=host)),
                      (u'No association ID',
                       u'No association ID found at {host}'.format(host=host))
                      ]

            fn_check = lambda out, err, text: (text not in out and
                                               text not in err)

            for check in checks:
                self.verify_response_true(fn_check(out, err, check[0]),
                                          check[1],
                                          step)

    def test_ntp_on_nodes(self):
        """Check NTP on controller and compute nodes
        Target component: Nova

        Scenario:
            1. Check NTP configuration on controller nodes
            2. Check NTP configuration on compute nodes

        Duration: 15 s.

        Available since release: 2015.1.0-8.0
        """

        for host in self.controllers:
            self._check_ntp(host, 1, 'controller')

        for host in self.computes:
            self._check_ntp(host, 2, 'compute')
