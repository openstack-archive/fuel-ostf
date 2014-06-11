# Copyright 2013 Mirantis, Inc.
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
import uuid

from fuel_health import murano

from fuel_health.common.utils.data_utils import rand_name


LOG = logging.getLogger(__name__)


class MuranoDeployLinuxServicesTests(murano.MuranoTest):
    """
    TestClass contains verifications of full Murano functionality.
    Special requirements:
        1. Murano component should be installed.
        2. Internet access for virtual machines in OpenStack.
        3. Linux image with Murano metadata should be imported.
    """

    def setUp(self):
        super(MuranoDeployLinuxServicesTests, self).setUp()
        self.check_clients_state()

        if not self.flavor_reqs:
            self.fail("This test requires more resources"
                      "on one of the compute nodes"
                      "(>2048MB of free RAM), but you have"
                      "only {0} MB of free RAM"
                      "on most appropriate"
                      "compute node".format(self.max_available_ram))

        msg = ("Linux image with Murano "
               "tag isn't available. Need to import this image into "
               "glance and mark with Murano metadata tag. Please refer to"
               " the Mirantis Open Stack and Murano user documentation. ")
        self.image = self.find_murano_image('linux')
        if not self.image:
            LOG.debug(msg)
            self.fail(msg)

    def test_deploy_telnet_service(self):
        """Check that user can deploy Telnet service in Murano environment
        Target component: Murano

        Scenario:
            1. Send request to create environment.
            2. Send request to create session for environment.
            3. Send request to create Linux-based service Telnet.
            4. Request to deploy session.
            5. Checking environment status.
            6. Checking deployments status
            7. Send request to delete environment.

        Duration: 920 s.

        Deployment tags: Murano, Heat
        """

        fail_msg = "Can't create environment. Murano API is not available. "
        self.environment = self.verify(15, self.create_environment,
                                       1, fail_msg, 'creating environment',
                                       self.env_name)

        fail_msg = "User can't create session for environment. "
        session = self.verify(5, self.create_session,
                              2, fail_msg, "session creating",
                              self.environment['id'])

        post_body = {
            "instance": {
                "flavor": self.flavor_name,
                "image": self.image.name,
                "?": {
                    "type": "io.murano.resources.Instance",
                    "id": str(uuid.uuid4())
                },
                "name": rand_name("testMurano")
            },
            "name": rand_name("teMurano"),
            "?": {
                "_{id}".format(id=uuid.uuid4().hex): {
                    "name": "Telnet"
                },
                "type": "io.murano.apps.linux.Telnet",
                "id": str(uuid.uuid4())
            }
        }

        fail_msg = "User can't create service. "
        self.verify(5, self.create_service,
                    3, fail_msg, "service creating",
                    self.environment['id'], session['id'], post_body)

        fail_msg = "User can't deploy session. "
        self.verify(5, self.deploy_session,
                    4, fail_msg,
                    "sending session on deployment",
                    self.environment['id'], session['id'])

        fail_msg = "Deployment was not completed correctly. "
        self.verify(900, self.deploy_check,
                    5, fail_msg, 'deployment is going',
                    self.environment['id'])

        self.verify(5, self.deployments_status_check,
                    6, fail_msg,
                    'Check deployments status',
                    self.environment['id'])

        fail_msg = "Can't delete environment. "
        self.verify(5, self.delete_environment,
                    7, fail_msg, "deleting environment",
                    self.environment['id'])

    def test_deploy_apache_service(self):
        """Check that user can deploy Apache service in Murano environment
        Target component: Murano

        Scenario:
            1. Send request to create environment.
            2. Send request to create session for environment.
            3. Send request to create Linux-based service Apache.
            4. Request to deploy session.
            5. Checking environment status.
            6. Checking deployments status
            7. Send request to delete environment.

        Duration: 920 s.

        Deployment tags: Murano, Heat
        """

        fail_msg = "Can't create environment. Murano API is not available. "
        self.environment = self.verify(15, self.create_environment,
                                       1, fail_msg, 'creating environment',
                                       self.env_name)

        fail_msg = "User can't create session for environment. "
        session = self.verify(5, self.create_session,
                              2, fail_msg, "session creating",
                              self.environment['id'])

        post_body = {
            "instance": {
                "flavor": self.flavor_name,
                "image": self.image.name,
                "?": {
                    "type": "io.murano.resources.Instance",
                    "id": str(uuid.uuid4())
                },
                "name": rand_name("testMurano")
            },
            "name": rand_name("teMurano"),
            "?": {
                "_{id}".format(id=uuid.uuid4().hex): {
                    "name": "Apache"
                },
                "type": "io.murano.apps.apache.Apache",
                "id": str(uuid.uuid4())
            }
        }

        fail_msg = "User can't create service. "
        self.verify(5, self.create_service,
                    3, fail_msg, "service creating",
                    self.environment['id'], session['id'], post_body)

        fail_msg = "User can't deploy session. "
        self.verify(5, self.deploy_session,
                    4, fail_msg,
                    "sending session on deployment",
                    self.environment['id'], session['id'])

        fail_msg = "Deployment was not completed correctly. "
        self.verify(900, self.deploy_check,
                    5, fail_msg, 'deployment is going',
                    self.environment['id'])

        self.verify(5, self.deployments_status_check,
                    6, fail_msg,
                    'Check deployments status',
                    self.environment['id'])

        fail_msg = "Can't delete environment. "
        self.verify(5, self.delete_environment,
                    7, fail_msg, "deleting environment",
                    self.environment['id'])
