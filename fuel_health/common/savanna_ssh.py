# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Mirantis, Inc.
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

import logging
import paramiko

from fuel_health.exceptions import SSHExecCommandFailed

import fuel_health.config

LOG = logging.getLogger(__name__)


def ssh_command(cmd):
    config = fuel_health.config.FuelConfig()
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    LOG.debug('Remote ssh commad is "%s"', cmd)
    try:
        ssh.connect(hostname=config.compute.controller_nodes[0],
                    username=config.compute.controller_node_ssh_user,
                    key_filename=config.compute.path_to_private_key,
                    timeout=300)
        _, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read()
        output_err = stderr.read()
        ssh.close()
        LOG.debug('Output ssh is "%s%s"', output, output_err)
        return output, output_err
    except SSHExecCommandFailed as exc:
        output_msg = "Command failed."
        LOG.debug(exc)
        LOG.debug(output_msg)
        raise exc
