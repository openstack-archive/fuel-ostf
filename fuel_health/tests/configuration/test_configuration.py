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
import paramiko.ssh_exception as exc

from fuel_health.common.ssh import Client as SSHClient
from fuel_health import exceptions
from fuel_health import nmanager
from keystoneclient.openstack.common.apiclient.exceptions import Unauthorized
from keystoneclient.v2_0 import Client as keystoneclient

LOG = logging.getLogger(__name__)


class SanityConfigurationTest(nmanager.SanityChecksTest):
    """TestClass contains tests for default creadentials usage.
    Special requirements:
        1. A controller's IP address should be specified.
        2. A compute's IP address should be specified.
        3. SSH user credentials for the controller and the compute
           should be specified in the controller_node_ssh_user parameter
    """

    @classmethod
    def setUpClass(cls):
        super(SanityConfigurationTest, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        pass

    def test_001_check_default_master_node_credential_usage(self):
        """Check usage of default credentials on master node
        Target component: Configuration

        Scenario:
            1. Check user can not ssh on master node with default credentials.
        Duration: 20 s.
         Available since release: 2014.2-6.1
        """

        ssh_client = SSHClient('localhost',
                               self.config.master.master_node_ssh_user,
                               self.config.master.master_node_ssh_password,
                               timeout=self.config.master.ssh_timeout)
        cmd = "date"
        output = []
        try:
            output = ssh_client.exec_command(cmd)
            LOG.debug(output)
        except exceptions.SSHExecCommandFailed:
            self.verify_response_true(len(output) == 0,
                                      'Step 1 failed: Default credentials for '
                                      'ssh on master node were not changed')
        except exceptions.TimeoutException:
            self.verify_response_true(len(output) == 0,
                                      'Step 1 failed: Default credentials for '
                                      'ssh on master node were not changed')
        except exc.SSHException:
            self.verify_response_true(len(output) == 0,
                                      'Step 1 failed: Default credentials for '
                                      'ssh on master node were not changed')

        self.verify_response_true(len(output) == 0,
                                  'Step 1 failed: Default credentials for '
                                  'ssh on master node were not changed')

    def test_002_check_default_openstack_credential_usage(self):
        """Check usage of default credentials for Openstack cluster
        Target component: Configuration

        Scenario:
            1. Check default credentials for Openstack cluster are changed.
        Duration: 20 s.
         Available since release: 2014.2-6.1
        """
        cluster_data = {
            'password': self.config.identity.admin_password,
            'username': self.config.identity.admin_username,
            'tenant': self.config.identity.admin_tenant_name}

        for key in cluster_data:
            self.verify_response_body_not_equal(
                exp_content='admin',
                act_content=cluster_data[key],
                msg='Default credentials value for {0} is using. '
                'We kindly recommend to change all defaults'.format(key),
                failed_step='1')

    def test_003_check_default_keystone_credential_usage(self):
            """Check usage of default credentials for keystone on master node
            Target component: Configuration

            Scenario:
                1. Check default credentials for keystone on master node are
                 changed.
            Duration: 20 s.
             Available since release: 2015.1.0-7.0
            """

            usr = self.config.master.keystone_user
            pwd = self.config.master.keystone_password
            url = 'http://{0}:5000/v2.0'.format(self.config.nailgun_host)

            try:
                keystone = keystoneclient(username=usr,
                                          password=pwd,
                                          auth_url=url)
                keystone.authenticate()
            except Unauthorized:
                pass
            else:
                self.fail('Step 1 failed: Default credentials '
                          'for keystone on master node were not changed')
