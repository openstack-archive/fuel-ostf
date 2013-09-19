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

import murano

class ServicesTestJSON(murano.MuranoTest):
    """
    TestClass contains tests that check basic Murano functionality.
    """

    def test_list_environments(self):
        """List Of Environments
        Test checks that user can get list of environments.
        Target component: Murano

        Scenario:
            1. Send request to create environment.
            2. Request the list of environments.
            3. Clean up (delete environment).
        Duration: 5 s.
        """

        fail_msg = 'Environments list is unavailable.'
        environments = self.verify(5, self.list_environments,
                                   2, fail_msg, "environments listing")

        step = '2. Request the list of environments.'
        self.verify_elements_list(environments, ['id', 'name'],
                                  msg=fail_msg, failed_step=step)

        " Save info for tear down method "
        self.last_step = '3. Clean up (delete environment).'

    def test_create_and_delete_service(self):
        """Create And Delete Service
        Test checks that user can create service.
        Target component: Murano

        Scenario:
            1. Send request to create environment.
            2. Send request to create session for environment.
            3. Send request to create service.
            4. Request the list of services.
            5. Send request to delete service.
            6. Clean up (delete environment).
        Duration: 20 s.
        """

        fail_msg = 'User can not create session for environment.'
        session = self.verify(5, self.create_session,
                              2, fail_msg, "session creating",
                              self.environment.id)

        srv = {"name": "new_service", "type": "test", "units": [{},]}
        fail_msg = 'User can not create service.'
        service = self.verify(5, self.create_service,
                              3, fail_msg, "service creating",
                              self.environment.id, session.id, srv)

        step = '4. Request the list of services.'
        fail_msg = 'User can not get list of services.'
        services = self.verify(5, self.list_services,
                               4, fail_msg, "services listing",
                               self.environment.id, session.id)

        self.verify_elements_list(services, ['id', 'name'],
                                  msg='User can not get list of services',
                                  failed_step=step)

        fail_msg = 'User can not delete service.'
        response = self.verify(5, self.delete_service,
                               5, fail_msg, "service deleting",
                               self.environment.id, session.id, service.id)

        " Save info for tear down method "
        self.last_step = '6. Clean up (delete environment).'
