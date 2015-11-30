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


class VMBootTest(cloudvalidation.CloudValidationTest):
    """Cloud Validation Test class for VMs."""

    def _check_host_boot(self, host):
        """Test resume_guest_state_on_host_boot option on compute node.
            By default, this option is set to False.
        """

        err_msg = ('The option "resume_guest_state_on_host_boot" '
                   'is set to True at compute node {host}, so it can be '
                   'broken down by the paused VMs after host boot.'
                   ).format(host=host)

        cmd = ('grep ^[^#]*\s*resume_guests_state_on_host_boot\s*=\s*True '
               '/etc/nova/nova.conf')

        cmd_timeout = 5
        step = 1
        action = 'check host boot option'

        out, err = self.verify(cmd_timeout, self._run_ssh_cmd, step, err_msg,
                               action, host, cmd)

        auto_host_boot_disabled = not out and not err
        self.verify_response_true(auto_host_boot_disabled, err_msg, 1)

    def test_guests_state_on_host_boot(self):
        """Check host boot configuration on compute nodes
        Target component: Nova

        Scenario:
            1. Check host boot configuration on compute nodes

        Duration: 20 s.

        Deployment tags: disabled

        Available since release: liberty-8.0
        """

        for host in self.computes:
            self._check_host_boot(host)
