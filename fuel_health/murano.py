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

import muranoclient.v1.client
import nmanager


class MuranoTest(nmanager.OfficialClientTest):
    """
    Manager that provides access to the Murano python client for
    calling Murano API.
    """

    client = None
    insecure = False
    api_host = 'http://127.0.0.1:8082'

    def setUp(self):
        """
            This method allows to initialize authentication before
            each test case and define parameters of Murano API Service
            This method also create environment for all tests
        """

        super(MuranoTest, self).setUp()
        step='1. Send request to create environment. '

        " Get xAuth token from Keystone "
        self.token_id = self.manager._get_identity_client(
            self.config.identity.admin_username,
            self.config.identity.admin_password,
            self.config.identity.admin_tenant_name).auth_token

        " Get Murano API parameters "
        try:
            self.api_host = self.config.murano.api_url
            self.insecure = self.config.murano.insecure
        except:
            msg = ' Can not get Murano configuration parameters. '
            msg = ('Step %s failed: ' % str(step)) + msg
            self.fail(msg)

        self.murano_client = self._get_murano_client()

        self.environment = self.create_environment("ost1_test-Murano_env01")
        if not hasattr(self.environment, 'id'):
            msg = ('Step %s failed: ' % step) + 'Can not create environment.'
            self.fail(msg)

    def tearDown(self):
        """
            This method alows to clean up after each test.
            The main task for this method - delete environment after
            PASSED and FAILED tests.
        """

        result = self.delete_environment(self.environment.id)
        if result:
            msg = ' Can not delete environment. '
            msg = ('Step %s failed: ' % str(self.last_step)) + msg
            self.fail(msg)

    def _get_murano_client(self):
        """
            This method returns Murano API client
        """
        return muranoclient.v1.client.Client(endpoint=self.api_host,
                                             token=self.token_id,
                                             insecure=self.insecure)

    def verify_elements_list(self, elements, attrs, msg='', failed_step=''):
        """
        Method provides human readable message for the verification of
        list of elements with specific parameters
        :param elements: the list of elements from response
        :param attrs: required attributes for each element
        :param msg: message to be used instead the default one
        :param failed_step: step with failed action
        """
        if failed_step:
            msg = ('Step %s failed: ' % str(failed_step)) + msg

        if not elements:
            self.fail(msg)

        for element in elements:
            for attribute in attrs:
                if not hasattr(element, attribute):
                    self.fail(msg)

    def list_environments(self):
        """
            This method allows to get the list of environments.

            Returns the list of environments.
        """

        return self.murano_client.environments.list()

    def create_environment(self, name):
        """
            This method allows to create environment.

            Input parameters:
              name - Name of new environment

            Returns new environment.
        """

        return self.murano_client.environments.create(name)

    def get_environment(self, environment_id, session_id=None):
        """
            This method allows to get specific environment by ID.

            Input parameters:
              environment_id - ID of environment
              session_id - ID of session for this environment (optional)

            Returns specific environment.
        """

        return self.murano_client.environments.get(environment_id, session_id)

    def update_environment(self, environment_id, new_name):
        """
            This method allows to update specific environment by ID.

            Input parameters:
              environment_id - ID of environment
              new_name - New name for environment

            Returns new environment.
        """

        return self.murano_client.environments.update(environment_id, new_name)

    def delete_environment(self, environment_id):
        """
            This method allows to delete specific environment by ID.

            Input parameters:
              environment_id - ID of environment

            Returns None.
        """

        return self.murano_client.environments.delete(environment_id)

    def create_session(self, environment_id):
        """
            This method allows to create session for environment.

            Input parameters:
              environment_id - ID of environment

            Returns new session.
        """

        return self.murano_client.sessions.configure(environment_id)

    def get_session(self, environment_id, session_id):
        """
            This method allows to get specific session.

            Input parameters:
              environment_id - ID of environment
              session_id - ID of session for this environment

            Returns specific session.
        """

        return self.murano_client.sessions.get(environment_id, session_id)

    def delete_session(self, environment_id, session_id):
        """
            This method allows to delete session for environment.

            Input parameters:
              environment_id - ID of environment
              session_id - ID of session for this environment

            Returns None.
        """

        return self.murano_client.sessions.delete(environment_id, session_id)

    def deploy_session(self, environment_id, session_id):
        """
            This method allows to deploy session for environment.

            Input parameters:
              environment_id - ID of environment
              session_id - ID of session for this environment

            Returns specific session.
        """

        return self.murano_client.sessions.deploy(environment_id, session_id)

    def create_service(self, environment_id, session_id, json_data):
        """
            This method allows to create service.

            Input parameters:
              environment_id - ID of environment
              session_id - ID of session for this environment
              json_data - JSON with service description

            Returns specific service.
        """

        return self.murano_client.services.post(environment_id, path='/',
                                                data=json_data, session_id=session_id)

    def list_services(self, environment_id, session_id=None):
        """
            This method allows to get list of services.

            Input parameters:
              environment_id - ID of environment
              session_id - ID of session for this environment (optional)

            Returns list of services.
        """

        return self.murano_client.services.get(environment_id, '/', session_id)

    def get_service(self, environment_id, session_id, service_id):
        """
            This method allows to get service by ID.

            Input parameters:
              environment_id - ID of environment
              session_id - ID of session for this environment
              service_id - ID of service in this environment

            Returns specific service.
        """

        return self.murano_client.services.get(environment_id,
                                               '/{0}'.format(service_id),
                                               session_id)

    def delete_service(self, environment_id, session_id, service_id):
        """
            This method allows to delete specific service.

            Input parameters:
              environment_id - ID of environment
              session_id - ID of session for this environment
              service_id - ID of service in this environment

            Returns None.
        """

        return self.murano_client.services.delete(environment_id,
                                                  '/{0}'.format(service_id),
                                                  session_id)
