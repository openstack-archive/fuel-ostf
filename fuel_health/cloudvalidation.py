# Copyright 2015 Mirantis, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_log import log as logging

LOG = logging.getLogger(__name__)

from fuel_health.common import ssh

from fuel_health import nmanager


class CloudValidationTest(nmanager.OfficialClientTest):
    """Base class for Cloud validation tests."""

    @classmethod
    def setUpClass(cls):
        super(CloudValidationTest, cls).setUpClass()
        if cls.manager.clients_initialized:
            cls.controllers = cls.config.compute.online_controllers
            cls.computes = cls.config.compute.online_computes
            cls.usr = cls.config.compute.controller_node_ssh_user
            cls.pwd = cls.config.compute.controller_node_ssh_password
            cls.key = cls.config.compute.path_to_private_key
            cls.timeout = cls.config.compute.ssh_timeout

    def setUp(self):
        super(CloudValidationTest, self).setUp()
        self.check_clients_state()

    def _run_ssh_cmd(self, host, cmd):
        """Open SSH session with host and execute command."""
        try:
            sshclient = ssh.Client(host, self.usr, self.pwd,
                                   key_filename=self.key, timeout=self.timeout)
            return sshclient.exec_longrun_command(cmd)
        except Exception:
            LOG.exception('Failure on ssh run cmd')
            self.fail("%s command failed." % cmd)
