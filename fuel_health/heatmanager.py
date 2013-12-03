# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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
import os
import warnings

from fuel_health.common.utils.data_utils import rand_name
import fuel_health.nmanager
import fuel_health.test

from fuel_health.exceptions import SSHExecCommandFailed

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import paramiko

LOG = logging.getLogger(__name__)


class HeatBaseTest(fuel_health.nmanager.OfficialClientTest):
    """
    Base class for Heat openstack sanity and smoke tests.
    """

    @classmethod
    def setUpClass(cls):
        super(HeatBaseTest, cls).setUpClass()
        cls.wait_interval = cls.config.compute.build_interval
        cls.wait_timeout = cls.config.compute.build_timeout
        cls.stacks = []

    @classmethod
    def tearDownClass(cls):
        super(HeatBaseTest, cls).tearDownClass()
        cls._clean_stacks()

    def setUp(self):
        super(HeatBaseTest, self).setUp()
        if self.heat_client is None:
            self.fail('Heat is unavailable.')

    @classmethod
    def _clean_stacks(cls):
        try:
            existing_stacks = [s.stack_name
                               for s in cls._list_stacks(cls.heat_client)]
            for stack in cls.stacks:
                if stack.stack_name in existing_stacks:
                    cls.heat_client.stacks.delete(stack.id)
        except Exception as exc:
            cls.error_msg.append(exc)
            LOG.debug(exc)

    @staticmethod
    def _list_stacks(client):
        return client.stacks.list()

    def _find_stack(self, client, key, value):
        for stack in self._list_stacks(client):
            if hasattr(stack, key) and getattr(stack, key) == value:
                return stack
        return None

    def _create_stack(self, client, template,
                      disable_rollback=True, parameters={}):

        stack_name = rand_name('ost1_test-')
        client.stacks.create(stack_name=stack_name,
                             template=template,
                             parameters=parameters,
                             disable_rollback=disable_rollback)
        # heat client doesn't return stack details after creation
        # so need to request them:
        stack = self._find_stack(client, 'stack_name', stack_name)
        self.stacks.append(stack)
        return stack

    def _update_stack(self, client, stack_id, template, parameters={}):
        client.stacks.update(stack_id=stack_id,
                             template=template,
                             parameters=parameters)
        return self._find_stack(client, 'id', stack_id)

    def _wait_for_stack_status(self, stack_id, expected_status,
                               timeout=None, interval=None):
        """
        The method is a customization of test.status_timeout().
        It addresses `stack_status` instead of `status` field.
        The rest is the same.
        """
        if timeout is None:
            timeout = self.wait_timeout
        if interval is None:
            interval = self.wait_interval

        def check_status():
            stack = self.heat_client.stacks.get(stack_id)
            new_status = stack.stack_status
            if new_status == 'ERROR':
                self.fail("Failed to get to expected status. In ERROR state.")
            elif new_status == expected_status:
                return True  # All good.
            LOG.debug("Waiting for %s to get to %s status. "
                      "Currently in %s status",
                      stack, expected_status, new_status)

        if not fuel_health.test.call_until_true(check_status,
                                                timeout,
                                                interval):
            self.fail("Timed out waiting to become %s"
                      % expected_status)

    def _wait_for_stack_deleted(self, stack_id):
        f = lambda: self._find_stack(self.heat_client, 'id', stack_id) is None
        if not fuel_health.test.call_until_true(f,
                                                self.wait_timeout,
                                                self.wait_interval):
            self.fail("Timed out waiting for stack to be deleted.")

    def _run_ssh_cmd(self, cmd):
        """
        Open SSH session with Controller and and execute command.
        """
        if not self.host:
            self.fail('Wrong tests configuration: '
                      'controller_nodes parameter is empty ')

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(hostname=self.host[0],
                        username=self.usr,
                        password=self.pwd,
                        key_filename=self.key,
                        timeout=self.timeout)
            _, stdout, stderr = ssh.exec_command(cmd)
            res = stdout.read()
            ssh.close()
            return res
        except SSHExecCommandFailed as exc:
            LOG.debug(exc)
            self.fail("%s command failed." % cmd)

    def _find_heat_image(self, image_name):
        return self.assertTrue(
            image_name in [
                i.name for i in self.compute_client.images.list()],
            "Image %s is not available in Glance." % image_name)

    def _wait_for_autoscaling(self, stack_name, exp_count,
                              timeout, interval):
        def count_instances():
            return len([i for i in self.compute_client.servers.list()
                        if i.name.startswith(stack_name)]) == exp_count

        return fuel_health.test.call_until_true(
            count_instances, timeout, interval)

    def _wait_for_cloudinit(self, conn_string, timeout, interval):
        """
        Wait for fake file (described in the stack template) to be created
        on the instance to make sure cloud-init procedure is completed.
        """
        cmd = (conn_string +
               " test -f /tmp/vm_ready.txt && echo -ne YES || echo -ne NO")

        def check():
            return self._run_ssh_cmd(cmd) == "YES"

        return fuel_health.test.call_until_true(
            check, timeout, interval)

    def _save_key_to_file(self, key):
        return self._run_ssh_cmd(
            "KEY=`mktemp`; echo '%s' > $KEY; echo -ne $KEY;" % key)

    def _delete_key_file(self, filepath):
        self._run_ssh_cmd("rm -f %s" % filepath)

    def _load_vm_cpu(self, connection_string):
        return self._run_ssh_cmd(
            connection_string + " cat /dev/urandom | gzip -9 > /dev/null &")

    def _release_vm_cpu(self, connection_string):
        return self._run_ssh_cmd(connection_string + " pkill cat")

    def _get_subnet_id(self):
        if 'neutron' in self.config.network.network_provider:
            networks = self.network_client.list_networks()
            net = [net for net in networks['networks']
                   if net['name'] == self.private_net]
            if len(net) == 0:
                self.fail('Wrong tests configuration: '
                          'network %s is not available.' % self.private_net)
            net = net[0]
            if 'subnets' in net and len(net['subnets']) > 0:
                return net['subnets'][0]
            else:
                return net.id

    def _load_template(self, base_file, file_name):
        filepath = os.path.join(
            os.path.dirname(os.path.realpath(base_file)),
            file_name)
        with open(filepath) as f:
            return f.read()

    def _customize_template(self, template):
        """
        By default, heat templates expect neutron subnets to be available.
        But if nova-network is used instead of neutron then
        subnet usage should be removed from the template.
        """
        return '\n'.join(line for line in template.splitlines()
                         if 'Ref: Subnet' not in line)