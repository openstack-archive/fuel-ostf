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
        cls.wait_interval = cls.config.compute.build_interval
        cls.wait_timeout = cls.config.compute.build_timeout
        cls.testvm_flavor = None
        cls.flavors = []

    def setUp(self):
        super(HeatBaseTest, self).setUp()
        if self.heat_client is None:
            self.fail('Heat is unavailable.')
        if not self.testvm_flavor:
            self.testvm_flavor = self._create_flavors(self.compute_client,
                                                      64, 1)

    def list_stacks(self, client):
        return client.stacks.list()

    def find_stack(self, client, key, value):
        for stack in self.list_stacks(client):
            if hasattr(stack, key) and getattr(stack, key) == value:
                return stack
        return None

    def create_stack(self, client, template,
                     disable_rollback=True, parameters={}):

        stack_name = rand_name('ost1_test-')
        client.stacks.create(stack_name=stack_name,
                             template=template,
                             parameters=parameters,
                             disable_rollback=disable_rollback)
        # heat client doesn't return stack details after creation
        # so need to request them:
        stack = self.find_stack(client, 'stack_name', stack_name)
        self.set_resource(stack.id, stack)
        return stack

    def update_stack(self, client, stack_id, template, parameters={}):
        client.stacks.update(stack_id=stack_id,
                             template=template,
                             parameters=parameters)
        return self.find_stack(client, 'id', stack_id)

    def wait_for_stack_status(self, stack_id, expected_status):
        """
        The method is a customization of test.status_timeout().
        It addresses `stack_status` instead of `status` field.
        The rest is the same.
        """

        def check_status():
            stack = self.heat_client.stacks.get(stack_id)
            new_status = stack.stack_status
            if new_status == 'CREATE_FAILED':
                self.fail("Failed to get to expected status. "
                          "In CREATE_FAILED state.")
            elif new_status == expected_status:
                return True  # All good.
            LOG.debug("Waiting for %s to get to %s status. "
                      "Currently in %s status",
                      stack, expected_status, new_status)

        if not fuel_health.test.call_until_true(check_status,
                                                self.wait_timeout,
                                                self.wait_interval):
            self.fail("Timed out waiting to become %s"
                      % expected_status)

    def wait_for_stack_deleted(self, stack_id):
        f = lambda: self.find_stack(self.heat_client, 'id', stack_id) is None
        if not fuel_health.test.call_until_true(f,
                                                self.wait_timeout,
                                                self.wait_interval):
            self.fail("Timed out waiting for stack to be deleted.")

    def run_ssh_cmd(self, cmd):
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

    def get_subnet_id(self):
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

            subnet = self.run_ssh_cmd(cmd)
            if subnet:
                return subnet
                # if network has no subnets
            networks = [net.id for net in
                        self.compute_client.networks.list()
                        if net.label == self.private_net]
            return networks[0]

    @staticmethod
    def customize_template(template):
        """
        By default, heat templates expect neutron subnets to be available.
        But if nova-network is used instead of neutron then
        subnet usage should be removed from the template.
        """
        return '\n'.join(line for line in template.splitlines()
                         if 'Ref: Subnet' not in line)