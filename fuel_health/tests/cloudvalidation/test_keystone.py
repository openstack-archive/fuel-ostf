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


class KeystoneTest(cloudvalidation.CloudValidationTest):
    """Cloud Validation Test class for Keystone service."""

    LOGFILE = '/var/log/keystone/keystone-all.log'
    PAT_SSL = ('Signing error: Error opening signer certificate '
               '(.+)signing_cert.pem')

    def _check_ssl_issue(self, host):
        """Check SSL issue on controller node."""

        cmd = 'grep -E "{pattern}" "{logfile}"'.format(pattern=self.PAT_SSL,
                                                       logfile=self.LOGFILE)

        err_msg = "Cannot check Keystone logs on host {host}".format(host=host)

        out, err = self.verify(5, self._run_ssh_cmd, 1, err_msg,
                               'check ssl certificate on host', host, cmd)

        return bool(out)

    def test_keystone_ssl_certificate(self):
        """Check Keystone SSL certificate
        Target component: Keystone

        Scenario:
            1. Check Keystone SSL certificate

        Duration: 20 s.

        Available since release: 2015.1.0-8.0
        """

        hosts = filter(self._check_ssl_issue,
                       self.controllers)

        err_msg = "Keystone SSL issue found on host(s): %s" % hosts

        self.verify_response_true(not hosts, err_msg, 1)
