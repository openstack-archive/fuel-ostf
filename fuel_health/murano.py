# Copyright 2013 Mirantis, Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
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
import requests
import time
import traceback

import muranoclient.common.exceptions as exceptions
from fuel_health.common.utils.data_utils import rand_name
import fuel_health.nmanager

LOG = logging.getLogger(__name__)


class MuranoTest(fuel_health.nmanager.PlatformServicesBaseClass):
    """
    Manager that provides access to the Murano python client for
    calling Murano API.
    """

    def setUp(self):
        super(MuranoTest, self).setUp()
        self.check_clients_state()
        self.env_name = rand_name("ostf_test-Murano_env")

        if not self.config.compute.compute_nodes \
                and self.config.compute.libvirt_type != 'vcenter':
            self.skipTest('There are no compute nodes')

        self.min_required_ram = 2048
        self.max_available_ram, self.flavor_reqs = (
            self.check_compute_node_ram(self.min_required_ram))

        self.murano_available = True
        self.endpoint = self.config.murano.api_url + '/v1/'
        self.headers = {'X-Auth-Token': self.murano_client.auth_token,
                        'content-type': 'application/json'}
        try:
            self.list_environments()
        except exceptions.CommunicationError:
            self.murano_available = False
            self.skipTest("Murano service is not available")

    def tearDown(self):
        """
            This method allows to clean up the OpenStack environment
            after the Murano OSTF tests.
        """

        if self.murano_available:
            for env in self.list_environments()["environments"]:
                if self.env_name in env["name"]:
                    try:
                        self.delete_environment(env["id"])
                    except:
                        LOG.warning(traceback.format_exc())

        super(MuranoTest, self).tearDown()

    def find_murano_image(self, image_type):
        """
            This method allows to find Windows images with Murano tag.

            Returns the image object or None

            image_type should be in [linux, windows.2012, cirros.demo]
        """

        tag = 'murano_image_info'

        for image in self.compute_client.images.list():
            if tag in image.metadata:
                metadata = json.loads(image.metadata[tag])
                if image_type == metadata['type']:
                    return image

    def list_environments(self):
        """
            This method allows to get the list of environments.

            Returns the list of environments.
        """

        resp = requests.get(self.endpoint + 'environments',
                            headers=self.headers)
        return resp.json()

    def create_environment(self, name):
        """
            This method allows to create environment.

            Input parameters:
              name - Name of new environment

            Returns new environment.
        """

        post_body = {'name': name}
        resp = requests.post(self.endpoint + 'environments',
                             data=json.dumps(post_body),
                             headers=self.headers)
        return resp.json()

    def get_environment(self, environment_id):
        """
            This method allows to get specific environment by ID.

            Input parameters:
              environment_id - ID of environment
              session_id - ID of session for this environment (optional)

            Returns specific environment.
        """

        return requests.get('{0}environments/{1}'.format(self.endpoint,
                                                         environment_id),
                            headers=self.headers).json()

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

        endpoint = '{0}environments/{1}'.format(self.endpoint, environment_id)
        resp = requests.delete(endpoint, headers=self.headers)
        return resp

    def create_session(self, environment_id):
        """
            This method allows to create session for environment.

            Input parameters:
              environment_id - ID of environment

            Returns new session.
        """

        post_body = None
        endpoint = '{0}environments/{1}/configure'.format(self.endpoint,
                                                          environment_id)
        return requests.post(endpoint, data=post_body,
                             headers=self.headers).json()

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

        endpoint = '{0}environments/{1}/sessions/{2}/deploy'.format(
            self.endpoint, environment_id, session_id)
        return requests.post(endpoint, data=None, headers=self.headers)

    def create_service(self, environment_id, session_id, json_data):
        """
            This method allows to create service.

            Input parameters:
              environment_id - ID of environment
              session_id - ID of session for this environment
              json_data - JSON with service description

            Returns specific service.
        """
        headers = self.headers.copy()
        headers.update({'x-configuration-session': session_id})
        endpoint = '{0}environments/{1}/services'.format(self.endpoint,
                                                         environment_id)
        return requests.post(endpoint, data=json.dumps(json_data),
                             headers=headers).json()

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

            Returns environment.
        """

        environment = self.get_environment(environment_id)
        while environment['status'] != 'ready':
            time.sleep(5)
            environment = self.get_environment(environment_id)
            if environment['status'] == 'deploy failure':
                LOG.error(
                    'Environment has incorrect status'
                    ' %s' % environment['status'])
                self.fail(
                    'Environment has incorrect status'
                    ' %s .' % environment['status'])
        return environment

    def deployments_status_check(self, environment_id):
        """
            This method allows to check that deployment status is 'success'.

            Input parameters:
              environment_id - ID of environment

            Returns 'OK'.
        """

        endpoint = '{0}environments/{1}/deployments'.format(self.endpoint,
                                                            environment_id)
        deployments = requests.get(endpoint,
                                   headers=self.headers).json()['deployments']
        for depl in deployments:
            # Save the information about all deployments
            LOG.debug("Environment state: {0}".format(depl['state']))
            r = requests.get('{0}/{1}'.format(endpoint, depl['id']),
                             headers=self.headers).json()
            LOG.debug("Reports: {0}".format(r))

            self.assertEqual('success', depl['state'])
        return 'OK'

    def ports_check(self, environment, ports):
        """
            This method allows to check that needed ports are opened.

            Input parameters:
              environment - Murano environment
              ports - list of needed ports

            Returns 'OK'.
        """
        check_ip = environment['services'][0]['instance']['floatingIpAddress']

        for port in ports:
            self.assertTrue(self._try_port(check_ip, port))

        return 'OK'

    def get_list_packages(self):
        resp = requests.get(self.endpoint + 'catalog/packages',
                            headers=self.headers)

        self.assertEqual(200, resp.status_code)
        self.assertIsInstance(resp.json()['packages'], list)

    def get_list_categories(self):
        resp = requests.get(self.endpoint + 'catalog/packages/categories',
                            headers=self.headers)

        self.assertEqual(200, resp.status_code)
        self.assertIsInstance(resp.json()['categories'], list)

    def check_path(self, environment, path):
        floating_ip = environment['services'][0]['instance'][
            'floatingIpAddress']
        resp = requests.get('http://{0}/{1}'.format(floating_ip, path))

        self.assertEqual(200, resp.status_code)
