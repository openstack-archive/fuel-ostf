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

import fuel_health.common.ssh
from fuel_health.common.utils.data_utils import rand_name
import fuel_health.nmanager
import fuel_health.test


LOG = logging.getLogger(__name__)


class HeatBaseTest(fuel_health.nmanager.NovaNetworkScenarioTest):
    """Base class for Heat openstack sanity and smoke tests."""

    @classmethod
    def setUpClass(cls):
        super(HeatBaseTest, cls).setUpClass()
        if cls.manager.clients_initialized:
            if cls.heat_client is None:
                cls.fail('Heat is unavailable.')
            cls.wait_interval = cls.config.compute.build_interval
            cls.wait_timeout = cls.config.compute.build_timeout

    @classmethod
    def tearDownClass(cls):
        super(HeatBaseTest, cls).tearDownClass()

    def setUp(self):
        super(HeatBaseTest, self).setUp()
        self.check_clients_state()
        if not self.find_micro_flavor():
            self.fail('m1.micro flavor was not created.')

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
        """The method is a customization of test.status_timeout().
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
            if 'FAIL' in new_status:
                self.fail("Failed to get to expected status. "
                          "In %s state." % new_status)
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

    def _wait_for_autoscaling(self, exp_count,
                              timeout, interval, reduced_stack_name):
        LOG.info('expected count is {0}'.format(exp_count))

        def count_instances(reduced_stack_name):
            res = []
            _list = self.compute_client.servers.list()
            for server in _list:
                LOG.info('instance name is {0}'.format(server.name))
                if server.name.startswith(reduced_stack_name):
                    res.append(server)
                    LOG.info('!!! current res is {0}'.format(res))

            return len(res) == exp_count

        return fuel_health.test.call_until_true(
            count_instances, timeout, interval, reduced_stack_name)

    def _wait_for_vm_ready_for_load(self, conn_string, timeout, interval):
        """Wait for fake file to be created on the instance
        to make sure that vm is ready.
        """
        cmd = (conn_string +
               " 'touch /tmp/ostf-heat.txt; "
               "test -f /tmp/ostf-heat.txt && echo -ne YES || echo -ne NO'")

        def check():
            return self._run_ssh_cmd(cmd)[0] == "YES"

        return fuel_health.test.call_until_true(
            check, timeout, interval)

    def _save_key_to_file(self, key):
        return self._run_ssh_cmd(
            "KEY=`mktemp`; echo '%s' > $KEY; "
            "chmod 600 $KEY; echo -ne $KEY;" % key)[0]

    def _delete_key_file(self, filepath):
        self._run_ssh_cmd("rm -f %s" % filepath)

    def _load_vm_cpu(self, connection_string):
        self._run_ssh_cmd(connection_string + " 'rm -f /tmp/ostf-heat.txt'")
        return self._run_ssh_cmd(connection_string +
                                 " 'cat /dev/urandom |"
                                 " gzip -9 > /dev/null &'")[0]

    def _release_vm_cpu(self, connection_string):
        pid = self._run_ssh_cmd(connection_string +
                                ' ps -ef | grep \"cat /dev/urandom\" '
                                '| grep -v grep | awk \"{print $1}\"')[0]

        return self._run_ssh_cmd(connection_string +
                                 " kill -9 %s" % pid.strip())[0]

    @staticmethod
    def _load_template(file_name):
        """Load specified template file from etc directory."""
        filepath = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "etc", file_name)
        with open(filepath) as f:
            return f.read()

    @staticmethod
    def _customize_template(template):
        """By default, heat templates expect neutron subnets to be available.
        But if nova-network is used instead of neutron then
        subnet usage should be removed from the template.
        """
        return '\n'.join(line for line in template.splitlines()
                         if 'Ref: Subnet' not in line)

    def _get_stack_instances(self, mask_name):
        self.instances = []

        # find just created instance
        instance_list = self.compute_client.servers.list()
        LOG.info('Instances list is {0}'.format(instance_list))
        LOG.info('Expected instance name includes {0}'.format(mask_name))

        for inst in instance_list:
            LOG.info('Instance name is {0}'.format(inst.name))
            if inst.name.startswith(mask_name):
                self.instances.append(inst)

        return self.instances
