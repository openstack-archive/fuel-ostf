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


LOG = logging.getLogger(__name__)


class MuranoDeployDemoServiceTests(murano.MuranoTest):
    """
    Special requirements:
        1. Murano component should be installed.
        2. Demo image with Murano metadata should be imported.
    """

    def test_deploy_demo_service(self):
        """Check that user can deploy Demo service in Murano environment
        Target component: Murano

        Scenario:
            1. Check Demo image in Glance.
            2. Send request to create environment.
            3. Send request to create session for environment.
            4. Send request to create Linux-based service Demo.
            5. Request to deploy session.
            6. Checking environment status.
            7. Checking deployments status
            8. Send request to delete environment.

        Duration: 120 s.

        Deployment tags: Murano, Heat
        """

        fail_msg = ("Demo image with Murano tag isn't available. "
                    "This image should be imported into glance "
                    "during the Open Stack deployment by default. "
                    "Please refer to the Mirantis Open Stack "
                    "and Murano user documentation. ")
        demo_image = self.verify(10, self.find_murano_image,
                                 1, fail_msg, 'searching demo image',
                                 'cirros.demo')
        self.verify_response_true(demo_image, fail_msg, 1)

        fail_msg = "Can't create environment. Murano API is not available. "
        self.environment = self.verify(15, self.create_environment,
                                       2, fail_msg, 'creating environment',
                                       self.env_name)

        fail_msg = "User can't create session for environment. "
        session = self.verify(5, self.create_session,
                              3, fail_msg, "session creating",
                              self.environment.id)

        post_body = {
            '?': {
                'type': "io.murano.tests.demoService",
                'id': uuid.uuid4().hex
            },
            "availabilityZone": "nova",
            "name": "demo",
            "unitNamingPattern": "host",
            "osImage": {
                "type": "cirros.demo",
                "name": demo_image.name,
                "title": "Demo"
            },
            "units": [{}],
            "flavor": "m1.tiny",
            "configuration": "standalone"
        }

        fail_msg = "User can't create service. "
        self.verify(5, self.create_service,
                              4, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = "User can't deploy session. "
        self.verify(5, self.deploy_session,
                                  5, fail_msg,
                                  "sending session on deployment",
                                  self.environment.id, session.id)

        fail_msg = "Deployment was not completed correctly. "
        self.verify(900, self.deploy_check,
                                 6, fail_msg, 'deployment is going',
                                 self.environment.id)

        self.verify(5, self.deployments_status_check,
                                        7, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = "Can't delete environment. "
        self.verify(5, self.delete_environment,
                    7, fail_msg, "deleting environment",
                    self.environment.id)


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
            self.fail("This test requires more resources on compute node"
                      "(>=2048MB of free RAM)")

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
                              self.environment.id)

        post_body = {
            '?': {
                'type': "io.murano.tests.linuxTelnetService",
                'id': uuid.uuid4().hex
            },
            "availabilityZone": "nova",
            "name": "LinuxTelnet",
            "deployTelnet": True,
            "unitNamingPattern": "telnet",
            "keyPair": "",
            "osImage": {
                "type": "linux",
                "name": self.image.name,
                "title": "Linux Image"
            },
            "units": [{}],
            "flavor": self.flavor_name
        }

        fail_msg = "User can't create service. "
        self.verify(5, self.create_service,
                              3, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = "User can't deploy session. "
        self.verify(5, self.deploy_session,
                                  4, fail_msg,
                                  "sending session on deployment",
                                  self.environment.id, session.id)

        fail_msg = "Deployment was not completed correctly. "
        self.verify(900, self.deploy_check,
                                 5, fail_msg, 'deployment is going',
                                 self.environment.id)

        self.verify(5, self.deployments_status_check,
                                        6, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = "Can't delete environment. "
        self.verify(5, self.delete_environment,
                    7, fail_msg, "deleting environment",
                    self.environment.id)

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
                              self.environment.id)

        post_body = {
            '?': {
                'type': "io.murano.tests.linuxApacheService",
                'id': uuid.uuid4().hex
            },
            "availabilityZone": "nova",
            "name": "LinuxApache",
            "deployApachePHP": True,
            "unitNamingPattern": "apache",
            "keyPair": "",
            "instanceCount": [{}],
            "osImage": {
                "type": "linux",
                "name": self.image.name,
                "title": "Linux Image"
            },
            "units": [{}],
            "flavor": self.flavor_name
        }

        fail_msg = "User can't create service. "
        self.verify(5, self.create_service,
                              3, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = "User can't deploy session. "
        self.verify(5, self.deploy_session,
                                  4, fail_msg,
                                  "sending session on deployment",
                                  self.environment.id, session.id)

        fail_msg = "Deployment was not completed correctly. "
        self.verify(900, self.deploy_check,
                                 5, fail_msg, 'deployment is going',
                                 self.environment.id)

        self.verify(5, self.deployments_status_check,
                                        6, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = "Can't delete environment. "
        self.verify(5, self.delete_environment,
                    7, fail_msg, "deleting environment",
                    self.environment.id)

