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

import time

import fuel_health.nmanager


class MuranoTest(fuel_health.nmanager.OfficialClientTest):
    """
    Manager that provides access to the Murano python client for
    calling Murano API.
    """

    def setUp(self):
        """
            This method allows to initialize authentication before
            each test case and define parameters of Murano API Service
            This method also create environment for all tests
        """

        super(MuranoTest, self).setUp()

        if self.murano_client is None:
            self.fail('Murano is unavailable.')

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

    def check_image(self):
        fail_msg = ("Windows image 'ws-2012-std' with Murano tag wasn't"
                   " imported into Glance. Please refer to the "
                   "Fuel Web user documentation")
        action_msg = "checking if Windows image with Murano tag is available"
        def find_image(tag):
            for i in self.compute_client.images.list():
                if 'murano_image_info' in i.metadata and \
                'ws-2012-std' == i.name and \
                'ws-2012-std' == i.metadata[tag]['type']:
                    return True
            return False

        image = self.verify(20, find_image, 1, fail_msg,
                            action_msg, 'murano_image_info')

        if not image:
            self.fail(fail_msg)

    def is_keypair_available(self, keyname):
        return keyname in [k.id for k in self.compute_client.keypairs.list()]

    def list_environments(self):
        """
            This method allows to get the list of environments.

            Returns the list of environments.
        """
        msg = ("Can't get the list of environments. "
               "Murano API service isn't available. ")
        try:
            result = self.murano_client.environments.list()
            return result
        except:
            raise AssertionError(msg)

    def create_environment(self, name):
        """
            This method allows to create environment.

            Input parameters:
              name - Name of new environment

            Returns new environment.
        """
        msg = ("Can't create new environment. "
               "Murano API service isn't available. ")
        try:
            result = self.murano_client.environments.create(name)
            return result
        except:
            raise AssertionError(msg)

    def get_environment(self, environment_id, session_id=None):
        """
            This method allows to get specific environment by ID.

            Input parameters:
              environment_id - ID of environment
              session_id - ID of session for this environment (optional)

            Returns specific environment.
        """
        msg = ("Can't get the environment. "
               "Murano API service isn't available. ")
        try:
            result = self.murano_client.environments.get(environment_id,
                                                         session_id)
            return result
        except:
            raise AssertionError(msg)

    def update_environment(self, environment_id, new_name):
        """
            This method allows to update specific environment by ID.

            Input parameters:
              environment_id - ID of environment
              new_name - New name for environment

            Returns new environment.
        """
        msg = ("Can't update the environment. "
               "Murano API service isn't available. ")
        try:
            result = self.murano_client.environments.update(environment_id,
                                                            new_name)
            return result
        except:
            raise AssertionError(msg)

    def delete_environment(self, environment_id):
        """
            This method allows to delete specific environment by ID.

            Input parameters:
              environment_id - ID of environment

            Returns None.
        """
        msg = ("Can't delete the environment. "
               "Murano API service isn't available. ")
        try:
            self.murano_client.environments.delete(environment_id)
        except:
            raise AssertionError(msg)

    def create_session(self, environment_id):
        """
            This method allows to create session for environment.

            Input parameters:
              environment_id - ID of environment

            Returns new session.
        """
        msg = ("Can't create session for environment. "
               "Murano API service isn't available. ")
        try:
            result = self.murano_client.sessions.configure(environment_id)
            return result
        except:
            raise AssertionError(msg)

    def get_session(self, environment_id, session_id):
        """
            This method allows to get specific session.

            Input parameters:
              environment_id - ID of environment
              session_id - ID of session for this environment

            Returns specific session.
        """
        msg = ("Can't get session for environment. "
               "Murano API service isn't available. ")
        try:
            result = self.murano_client.sessions.get(environment_id,
                                                     session_id)
            return result
        except:
            raise AssertionError(msg)

    def delete_session(self, environment_id, session_id):
        """
            This method allows to delete session for environment.

            Input parameters:
              environment_id - ID of environment
              session_id - ID of session for this environment

            Returns None.
        """
        msg = ("Can't delete session for environment. "
               "Murano API service isn't available. ")
        try:
            result = self.murano_client.sessions.delete(environment_id,
                                                        session_id)
            return result
        except:
            raise AssertionError(msg)

    def deploy_session(self, environment_id, session_id):
        """
            This method allows to deploy session for environment.

            Input parameters:
              environment_id - ID of environment
              session_id - ID of session for this environment

            Returns specific session.
        """
        msg = ("Can't deploy session for environment. "
               "Murano API service isn't available. ")
        try:
            result = self.murano_client.sessions.deploy(environment_id,
                                                        session_id)
            return result
        except:
            raise AssertionError(msg)

    def create_service(self, environment_id, session_id, json_data):
        """
            This method allows to create service.

            Input parameters:
              environment_id - ID of environment
              session_id - ID of session for this environment
              json_data - JSON with service description

            Returns specific service.
        """
        msg = ("Can't create service. "
               "Murano API service isn't available. ")
        try:
            result = self.murano_client.services.post(environment_id,
                                                      path='/',
                                                      data=json_data,
                                                      session_id=session_id)
            return result
        except:
            raise AssertionError(msg)

    def list_services(self, environment_id, session_id=None):
        """
            This method allows to get list of services.

            Input parameters:
              environment_id - ID of environment
              session_id - ID of session for this environment (optional)

            Returns list of services.
        """
        msg = ("Can't get the list of services. "
               "Murano API service isn't available. ")
        try:
            result = self.murano_client.services.get(environment_id, '/',
                                                     session_id)
            return result
        except:
            raise AssertionError(msg)

    def get_service(self, environment_id, session_id, service_id):
        """
            This method allows to get service by ID.

            Input parameters:
              environment_id - ID of environment
              session_id - ID of session for this environment
              service_id - ID of service in this environment

            Returns specific service.
        """
        msg = ("Can't get the service. "
               "Murano API service isn't available. ")
        try:
            path = '/{0}'.format(service_id)
            result = self.murano_client.services.get(environment_id,
                                                     path, session_id)
            return result
        except:
            raise AssertionError(msg)

    def delete_service(self, environment_id, session_id, service_id):
        """
            This method allows to delete specific service.

            Input parameters:
              environment_id - ID of environment
              session_id - ID of session for this environment
              service_id - ID of service in this environment

            Returns None.
        """
        msg = ("Can't delete the service. "
               "Murano API service isn't available. ")
        try:
            path = '/{0}'.format(service_id)
            result = self.murano_client.services.delete(environment_id,
                                                        path, session_id)
            return result
        except:
            raise AssertionError(msg)

    def deploy_check(self, environment_id):
        """
            This method allows to wait for deployment of Murano evironments.

            Input parameters:
              environment_id - ID of environment

            Returns 'OK'.
        """
        msg = ("Can't get environment status. "
               "Murano API service isn't available. ")
        try:
            infa = self.get_environment(environment_id)
            while infa.status != 'ready':
                time.sleep(15)
                infa = self.get_environment(environment_id)
            return 'OK'
        except:
            raise AssertionError(msg)

    def deployments_status_check(self, environment_id):
        """
            This method allows to check that deployment status is 'success'.

            Input parameters:
              environment_id - ID of environment

            Returns 'OK'.
        """
        msg = ("Can't get deployment status. "
               "Murano API service isn't available. ")
        try:
            deployments = self.murano_client.deployments.list(environment_id)
        except:
            raise AssertionError(msg)

        for depl in deployments:
            assert depl.state == 'success'
        return 'OK'
