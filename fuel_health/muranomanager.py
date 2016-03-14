# Copyright 2013 Mirantis, Inc.
# All Rights Reserved.
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

import contextlib
import logging
import os
import time
import traceback
import zipfile

try:
    from oslo.serialization import jsonutils
except ImportError:
    from oslo_serialization import jsonutils

import muranoclient.common.exceptions as exceptions
import requests

from fuel_health.common.utils.data_utils import rand_name
import fuel_health.nmanager

LOG = logging.getLogger(__name__)


class MuranoTest(fuel_health.nmanager.PlatformServicesBaseClass):
    """Manager that provides access to the Murano python client for
    calling Murano API.
    """
    @classmethod
    def setUpClass(cls):
        super(MuranoTest, cls).setUpClass()
        cls.packages = []
        cls.environments = []

    def setUp(self):
        super(MuranoTest, self).setUp()
        self.check_clients_state()
        self.env_name = rand_name("ostf_test-Murano_env")

        if not self.config.compute.compute_nodes:
            self.skipTest('There are no compute nodes to run tests')

        self.min_required_ram_mb = 4096

        self.murano_available = True
        self.endpoint = '{0}/v1/'.format(
            self.identity_client.service_catalog.url_for(
                service_type='application-catalog',
                endpoint_type='publicURL'))

        self.headers = {
            'X-Auth-Token': self.murano_client.http_client.auth_token,
            'content-type': 'application/json'
        }

        try:
            self.list_environments()
        except exceptions.CommunicationError:
            self.murano_available = False
            self.skipTest("Murano service is not available")

    def tearDown(self):
        """This method allows to clean up the OpenStack environment
        after the Murano OSTF tests.
        """

        if self.murano_available:
            if self.environments:
                for environment_id in self.environments:
                    try:
                        self.delete_environment(environment_id)
                    except Exception:
                        LOG.warning(traceback.format_exc())
            if self.packages:
                for package in self.packages:
                    try:
                        self.delete_package(package.id)
                    except Exception:
                        LOG.warning(traceback.format_exc())

        super(MuranoTest, self).tearDown()

    def zip_dir(self, parent_dir, app_dir):
        """This method allows to zip directory with application
        :param parent_dir: Directory, where application lives
        :param app_dir: Directory with application
        :return:
        """
        abs_path = os.path.join(parent_dir, app_dir)
        path_len = len(abs_path) + 1
        zip_file = abs_path + ".zip"
        with contextlib.closing(zipfile.ZipFile(zip_file, "w")) as zf:
            for dir_name, _, files in os.walk(abs_path):
                for filename in files:
                    fn = os.path.join(dir_name, filename)
                    zf.write(fn, fn[path_len:])
        return zip_file

    def find_murano_image(self, image_type):
        """This method allows to find Windows images with Murano tag.

        Returns the image object or None

        image_type should be in [linux, windows.2012, cirros.demo]
        """

        tag = 'murano_image_info'

        for image in self.compute_client.images.list():
            if tag in image.metadata and image.status.lower() == 'active':
                metadata = jsonutils.loads(image.metadata[tag])
                if image_type == metadata['type']:
                    return image

    def list_environments(self):
        """This method allows to get the list of environments.

        Returns the list of environments.
        """

        resp = requests.get(self.endpoint + 'environments',
                            headers=self.headers, verify=False)
        return resp.json()

    def create_environment(self, name):
        """This method allows to create environment.

        Input parameters:
          name - Name of new environment

        Returns new environment.
        """

        environment = self.murano_client.environments.create({'name': name})
        self.environments.append(environment.id)
        return environment

    def get_environment(self, environment_id):
        """This method allows to get specific environment by ID.

        Input parameters:
          environment_id - ID of environment
          session_id - ID of session for this environment (optional)

        Returns specific environment.
        """

        return self.murano_client.environments.get(environment_id)

    def update_environment(self, environment_id, new_name):
        """This method allows to update specific environment by ID.

        Input parameters:
          environment_id - ID of environment
          new_name - New name for environment

        Returns new environment.
        """

        return self.murano_client.environments.update(environment_id, new_name)

    def delete_environment(self, environment_id):
        """This method allows to delete specific environment by ID.

        Input parameters:
          environment_id - ID of environment

        Returns None.
        """

        self.murano_client.environments.delete(environment_id)
        return self.environments.remove(environment_id)

    def environment_delete_check(self, environment_id, timeout=60):
        resp = requests.get('{0}environments/{1}'.format(self.endpoint,
                                                         environment_id),
                            headers=self.headers, verify=False)
        self.delete_environment(environment_id)
        point = time.time()
        while resp.status_code == 200:
            if time.time() - point > timeout:
                self.fail("Can't delete environment more than {0} seconds".
                          format(timeout))
            resp = requests.get('{0}environments/{1}'.format(self.endpoint,
                                                             environment_id),
                                headers=self.headers, verify=False)
            try:
                env = resp.json()
                if env["status"] == "delete failure":
                    self.fail("Environment status: {0}".format(env["status"]))
            except Exception:
                LOG.debug("Failed to get environment status "
                          "or environment no more exists")
            time.sleep(5)

    def create_session(self, environment_id):
        """This method allows to create session for environment.

        Input parameters:
          environment_id - ID of environment

        Returns new session.
        """

        return self.murano_client.sessions.configure(environment_id)

    def get_session(self, environment_id, session_id):
        """This method allows to get specific session.

        Input parameters:
          environment_id - ID of environment
          session_id - ID of session for this environment

        Returns specific session.
        """

        return self.murano_client.sessions.get(environment_id, session_id)

    def delete_session(self, environment_id, session_id):
        """This method allows to delete session for environment.

        Input parameters:
          environment_id - ID of environment
          session_id - ID of session for this environment

        Returns None.
        """

        return self.murano_client.sessions.delete(environment_id, session_id)

    def deploy_session(self, environment_id, session_id):
        """This method allows to deploy session for environment.

        Input parameters:
          environment_id - ID of environment
          session_id - ID of session for this environment

        Returns specific session.
        """

        endpoint = '{0}environments/{1}/sessions/{2}/deploy'.format(
            self.endpoint, environment_id, session_id)
        return requests.post(endpoint, data=None, headers=self.headers,
                             verify=False)

    def create_service(self, environment_id, session_id, json_data):
        """This method allows to create service.

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
        return requests.post(endpoint, data=jsonutils.dumps(json_data),
                             headers=headers, verify=False).json()

    def list_services(self, environment_id, session_id=None):
        """This method allows to get list of services.

        Input parameters:
          environment_id - ID of environment
          session_id - ID of session for this environment (optional)

        Returns list of services.
        """

        return self.murano_client.services.get(environment_id, '/', session_id)

    def get_service(self, environment_id, session_id, service_id):
        """This method allows to get service by ID.

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
        """This method allows to delete specific service.

        Input parameters:
          environment_id - ID of environment
          session_id - ID of session for this environment
          service_id - ID of service in this environment

        Returns None.
        """

        return self.murano_client.services.delete(environment_id,
                                                  '/{0}'.format(service_id),
                                                  session_id)

    def deploy_check(self, environment):
        """This method allows to wait for deployment of Murano evironments.

        Input parameters:
          environment - Murano environment

        Returns environment.
        """

        environment = self.get_environment(environment.id)
        while environment.status != 'ready':
            time.sleep(5)
            environment = self.get_environment(environment.id)
            if environment.status == 'deploy failure':
                LOG.error(
                    'Environment has incorrect status'
                    ' %s' % environment.status)
                self.fail(
                    'Environment has incorrect status'
                    ' %s .' % environment.status)
        return environment

    def deployments_status_check(self, environment_id):
        """This method allows to check that deployment status is 'success'.

        Input parameters:
          environment_id - ID of environment

        Returns 'OK'.
        """

        endpoint = '{0}environments/{1}/deployments'.format(self.endpoint,
                                                            environment_id)
        deployments = requests.get(endpoint,
                                   headers=self.headers,
                                   verify=False).json()['deployments']
        for deployment in deployments:
            # Save the information about all deployments
            LOG.debug("Environment state: {0}".format(deployment['state']))
            r = requests.get('{0}/{1}'.format(endpoint, deployment['id']),
                             headers=self.headers, verify=False).json()
            LOG.debug("Reports: {0}".format(r))

            self.assertEqual('success', deployment['state'])
        return 'OK'

    def check_port_access(self, ip, port):
        output = ''
        start_time = time.time()
        while time.time() - start_time < 600:
            # Check VM port availability from controller node:
            output, err = self._run_ssh_cmd("nc -z {0} {1}; echo $?"
                                            .format(ip, port))
            if '0' in output:
                break
            time.sleep(5)
        self.assertIn('0', output, '%s port is closed on instance' % port)

    def port_status_check(self, environment, configurations):
        """Function which gives opportunity to check multiple instances
        :param environment: Murano environment
        :param configurations: Array of configurations.

        Example: [[instance_name, *ports], [instance_name, *ports]] ...
        """
        for configuration in configurations:
            inst_name = configuration[0]
            ports = configuration[1:]
            ip = self.get_ip_by_instance_name(environment, inst_name)
            if ip and ports:
                for port in ports:
                    self.check_port_access(ip, port)
            else:
                self.fail('Instance does not have floating IP')

    def get_ip_by_instance_name(self, environment, inst_name):
        """Returns ip of instance using instance name
        :param environment: Murano environment
        :param name: String, which is substring of name of instance or name of
        instance
        :return:
        """
        for service in environment.services:
            if inst_name in service['instance']['name']:
                return service['instance']['floatingIpAddress']

    def get_list_packages(self, artifacts=False):
        try:
            if artifacts:
                packages_list = self.murano_art_client.packages.list()
                packages = []
                for package in packages_list:
                    packages.append(package)
            else:
                packages_list = self.murano_client.packages.list()
                packages = list(packages_list)
        except exceptions.ClientException:
            self.fail("Can not get list of packages")
        LOG.debug('Packages List: {0}'.format(packages))
        self.assertIsInstance(packages, list)
        return packages

    def generate_fqn_list(self, artifacts=False):
        fqn_list = []
        packages = self.get_list_packages(artifacts)
        for package in packages:
            fqn_list.append(package.to_dict()['fully_qualified_name'])
        LOG.debug('FQN List: {0}'.format(fqn_list))
        return fqn_list

    def upload_package(self, package_name, body, app, artifacts=False):
        files = {'%s' % package_name: open(app, 'rb')}
        if artifacts:
            package = self.murano_art_client.packages.create(body, files)
        else:
            package = self.murano_client.packages.create(body, files)
        self.packages.append(package)
        return package

    def package_exists(self, artifacts=False, *packages):
        fqn_list = self.generate_fqn_list(artifacts)
        LOG.debug("Response for packages is {0}".format(fqn_list))
        for package in packages:
            if package not in fqn_list:
                return False
        return True

    def get_package(self, package_id, artifacts=False):
        if artifacts:
            package = self.murano_art_client.packages.get(package_id)
        else:
            package = self.murano_client.packages.get(package_id)
        return package

    def get_package_by_fqdn(self, package_name, artifacts=False):
        package_list = self.get_list_packages(artifacts)
        for package in package_list:
            if package.to_dict()["fully_qualified_name"] == package_name:
                return package

    def delete_package(self, package_id, artifacts=False):
        if artifacts:
            self.murano_art_client.packages.delete(package_id)
        else:
            self.murano_client.packages.delete(package_id)

    def get_list_categories(self):
        resp = requests.get(self.endpoint + 'catalog/packages/categories',
                            headers=self.headers, verify=False)

        self.assertEqual(200, resp.status_code)
        self.assertIsInstance(resp.json()['categories'], list)

    def check_path(self, env, path, inst_name=None):
        environment = env.manager.get(env.id)
        if inst_name:
            ip = self.get_ip_by_instance_name(environment, inst_name)
        else:
            ip = environment.services[0]['instance']['floatingIpAddress']
        uri = 'http://{0}/{1}'.format(ip, path)
        cmd = "curl --connect-timeout 1 --head {0}".format(uri)
        stdout, stderr = self._run_ssh_cmd(cmd)
        if '404' in stdout:
            self.fail("Service path unavailable")
