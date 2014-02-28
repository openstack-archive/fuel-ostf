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

import json
import logging
import time
import traceback

import muranoclient.common.exceptions as exceptions
from fuel_health.common.utils.data_utils import rand_name
import fuel_health.nmanager

LOG = logging.getLogger(__name__)


class MuranoTest(fuel_health.nmanager.OfficialClientTest):
    """
    Manager that provides access to the Murano python client for
    calling Murano API.
    """
    def setUp(self):
        super(MuranoTest, self).setUp()
        self.check_clients_state()
        self.env_name = rand_name(namestart="ost1_test-Murano_env")
        self.murano_available = True
        try:
            self.murano_client.environments.list()
        except exceptions.CommunicationError:
            self.murano_available = False
            self.fail("Murano service is not available")

    def tearDown(self):
        """
            This method allows to clean up the OpenStack environment
            after the Murano OSTF tests
        """
        super(MuranoTest, self).tearDown()
        if self.murano_available:
            for env in self.list_environments():
                if 'ost1_test-Murano_env' in env.name:
                    try:
                        self.delete_environment(env.id)
                    except:
                        LOG.warning(traceback.format_exc())

    def find_murano_image(self, image_type):
        """
            This method allows to find Windows images with Murano tag.

            Returns the image object or None

            image_type should be in [linux, windows.2012, cirros.demo]
        """
        for image in self.compute_client.images.list():
            tag = 'murano_image_info'
            if tag in image.metadata:
                metadata = json.loads(image.metadata[tag])
                if image_type == metadata['type']:
                    return image

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
                                                data=json_data,
                                                session_id=session_id)

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

    def deploy_check(self, environment_id):
        """
            This method allows to wait for deployment of Murano evironments.

            Input parameters:
              environment_id - ID of environment

            Returns 'OK'.
        """

        infa = self.get_environment(environment_id)
        while infa.status != 'ready':
            time.sleep(5)
            infa = self.get_environment(environment_id)
        return 'OK'

    def deployments_status_check(self, environment_id):
        """
            This method allows to check that deployment status is 'success'.

            Input parameters:
              environment_id - ID of environment

            Returns 'OK'.
        """

        deployments = self.murano_client.deployments.list(environment_id)
        for depl in deployments:
            # Save the information about all deployments
            LOG.debug("Environment state: {0}".format(depl.state))
            r = self.murano_client.deployments.reports(environment_id, depl.id)
            LOG.debug("Reports: {0}".format(r))

            assert depl.state == 'success'
        return 'OK'
