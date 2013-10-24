# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from fuel_health import murano


class MuranoSanityTests(murano.MuranoTest):
    """
    TestClass contains verifications of basic Murano functionality.
    Special requirements:
        1. Murano component should be installed.
    """

    def test_check_default_key_pair(self):
        """Check Murano Server Farms Default Key Pair 'murano-lb-key'
        Please, see more detailed information in Murano Administrator Guide.
        Target component: Murano

        Scenario:
            1. Check that Key Pair 'murano-lb-key' exists.

        Duration: 15 s.

        Deployment tags: Murano
        """

        fail_msg = ("Key Pair 'murano-lb-key' does not exist. Need to create "
                    "Key Pair manually. Please refer to the "
                    "Fuel Web user documentation")

        result = self.verify(15, self.is_keypair_available, 1, fail_msg,
                             "checking if 'murano-lb-key' is available",
                             'murano-lb-key')

        self.verify_response_true(result,
                                  "Step 1 failed: {msg}".format(msg=fail_msg))

    def test_check_windows_image_with_murano_tag(self):
        """Check Windows Image with Murano Tag availability
        Please, see more detailed information in Murano Administrator Guide.
        Target component: Murano

        Scenario:
            1. Check that image with Murano tag imported in Glance.

        Duration: 15 s.

        Deployment tags: Murano
        """

        fail_msg = ("Windows image 'ws-2012-std' with Murano tag wasn't"
                    " imported into Glance. Please refer to the "
                    "Fuel Web user documentation")
        action_msg = "checking if Windows image with Murano tag is available"

        def find_image(tag):
            for i in self.compute_client.images.list():
                if 'murano_image_info' in i.metadata:
                    return True
            return False

        image = self.verify(15, find_image, 1, fail_msg,
                            action_msg, 'murano_image_info')

        self.verify_response_true(image,
                                  "Step 1 failed: {msg}".format(msg=fail_msg))

    def test_create_and_delete_service(self):
        """Create, list and delete Murano environment and service
        Target component: Murano

        Scenario:
            1. Send request to create environment.
            2. Request the list of environments.
            3. Send request to create session for environment.
            4. Send request to create service.
            5. Request the list of services.
            6. Send request to delete service.
            7. Send request to delete environment.

        Duration: 140 s.

        Deployment tags: Murano
        """

        fail_msg = "Can't create environment. Murano API is not available. "
        self.environment = self.verify(20, self.create_environment,
                                       1, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = "Environments list is unavailable. "
        environments = self.verify(20, self.list_environments,
                                   2, fail_msg, "listing environments")

        step = "2. Request the list of environments. "
        self.verify_elements_list(environments, ['id', 'name'],
                                  msg=fail_msg, failed_step=step)

        fail_msg = "Can't create session for environment. "
        session = self.verify(20, self.create_session,
                              3, fail_msg, "creating session",
                              self.environment.id)

        srv = {"name": "new_service", "type": "test", "units": [{}, ]}
        fail_msg = "Can't create service. "
        service = self.verify(20, self.create_service,
                              4, fail_msg, "creating service",
                              self.environment.id, session.id, srv)

        step = '4. Request the list of services.'
        fail_msg = "Can't get list of services. "
        services = self.verify(20, self.list_services,
                               5, fail_msg, "listing services",
                               self.environment.id, session.id)

        self.verify_elements_list(services, ['id', 'name'],
                                  msg='Cannot get list of services',
                                  failed_step=step)

        fail_msg = "Can't delete service. "
        self.verify(20, self.delete_service,
                    6, fail_msg, "deleting service",
                    self.environment.id, session.id, service.id)

        fail_msg = "Can't delete environment. "
        self.verify(20, self.delete_environment,
                    7, fail_msg, "deleting environment",
                    self.environment.id)
