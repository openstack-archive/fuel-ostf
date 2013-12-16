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
import traceback

from fuel_health.common.utils.data_utils import rand_name
import fuel_health.common.ssh
import fuel_health.nmanager
import fuel_health.test

LOG = logging.getLogger(__name__)


class HeatBaseTest(fuel_health.nmanager.NovaNetworkScenarioTest,
                   fuel_health.nmanager.SmokeChecksTest):
    """
    Base class for Heat openstack sanity and smoke tests.
    """

    @classmethod
    def setUpClass(cls):
        fuel_health.nmanager.NovaNetworkScenarioTest.setUpClass()
        cls.flavors = []
        cls.wait_interval = cls.config.compute.build_interval
        cls.wait_timeout = cls.config.compute.build_timeout
        cls.testvm_flavor = None

    def setUp(self):
        super(HeatBaseTest, self).setUp()
        if self.heat_client is None:
            self.fail('Heat is unavailable.')
        if not self.testvm_flavor:
            self.testvm_flavor = self._create_flavors(self.compute_client,
                                                      64, 1)

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
        self.set_resource(stack.id, stack)
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
        It addresses `stack_status` instead of `status` field and
        checks for FAILED instead of ERROR status.
        The rest is the same.
        """
        if timeout is None:
            timeout = self.wait_timeout
        if interval is None:
            interval = self.wait_interval

        def check_status():
            stack = self.heat_client.stacks.get(stack_id)
            new_status = stack.stack_status
            if new_status == "CREATE_FAILED":
                self.fail("Failed to get to expected status. "
                          "In CREATE_FAILED state.")
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
        try:
            sshclient = fuel_health.common.ssh.Client(
                self.host[0], self.usr, self.pwd,
                key_filename=self.key, timeout=self.timeout
            )
            return sshclient.exec_longrun_command(cmd)
        except Exception as exc:
            LOG.debug(traceback.format_exc())
            self.fail("%s command failed." % cmd)

    def _find_heat_image(self, image_name):
        return image_name in [i.name for i in
                              self.compute_client.images.list()]

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
            neutron_net_list = ("neutron "
                                "--os-username=%s --os-password=%s "
                                "--os-tenant-name=%s --os-auth-url=%s "
                                "net-list" % (
                                    self.config.identity.admin_username,
                                    self.config.identity.admin_password,
                                    self.config.identity.admin_tenant_name,
                                    self.config.identity.uri))

            # net name surrounded with spaces to guarantee strict match
            grep = "%s | grep ' %s ' | grep -v grep | awk '{ print $6 }'" % (
                neutron_net_list, self.private_net)

            cmd = "echo -ne `%s`" % grep

            subnet = self._run_ssh_cmd(cmd)
            if subnet:
                return subnet
            # if network has no subnets
            networks = [net.id for net in
                        self.compute_client.networks.list()
                        if net.label == self.private_net]
            return networks[0]

    @staticmethod
    def _load_template(file_name):
        """
        Load specified template file from etc directory.
        """
        filepath = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "etc", file_name)
        with open(filepath) as f:
            return f.read()

    @staticmethod
    def _customize_template(template):
        """
        By default, heat templates expect neutron subnets to be available.
        But if nova-network is used instead of neutron then
        subnet usage should be removed from the template.
        """
        return '\n'.join(line for line in template.splitlines()
                         if 'Ref: Subnet' not in line)
