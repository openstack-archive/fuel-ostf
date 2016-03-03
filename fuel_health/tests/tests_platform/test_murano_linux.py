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
import os
import uuid

from fuel_health import muranomanager

from fuel_health.common.utils.data_utils import rand_name


LOG = logging.getLogger(__name__)


class MuranoDeployLinuxServicesTests(muranomanager.MuranoTest):
    """TestClass contains verifications of full Murano functionality.

    Special requirements:
        1. Murano component should be installed.
        2. Internet access for virtual machines in OpenStack.
        3. Linux image with Murano metadata should be imported.
    """

    def setUp(self):
        super(MuranoDeployLinuxServicesTests, self).setUp()
        self.check_clients_state()

        self.doc_link = 'https://www.fuel-infra.org/#fueldocs'

        self.image = self.find_murano_image('linux')

        self.dummy_fqdn = 'io.murano.apps.Simple'

        # Flavor with 2 vCPU and 40Gb HDD will allow to sucessfully
        # deploy all Murano applications.
        self.flavor_name = rand_name("ostf_test_Murano_flavor")
        flavor = self.compute_client.flavors.create(
            self.flavor_name, disk=40, ram=self.min_required_ram_mb, vcpus=2)
        self.addCleanup(self.compute_client.flavors.delete, flavor.id)

    def tearDown(self):
        super(MuranoDeployLinuxServicesTests, self).tearDown()

    def test_deploy_dummy_app(self):
        """Check that user can deploy application in Murano environment
        Target component: Murano

        Scenario:
            1. Prepare test app.
            2. Upload test app.
            3. Send request to create environment.
            4. Send request to create session for environment.
            5. Send request to create test service.
            6. Send request to deploy session.
            7. Checking environment status.
            8. Checking deployment status.
            9. Send request to delete environment.
            10. Send request to delete package.

        Duration: 1200 s.
        Deployment tags: Murano, Heat
        Available since release: 2014.2-6.1
        """

        vms_count = self.get_info_about_available_resources(
            self.min_required_ram_mb, 40, 2)
        if vms_count < 1:
            msg = ('This test requires more hardware resources of your '
                   'OpenStack cluster: your cloud should allow to create '
                   'at least 1 VM with {0} MB of RAM, {1} HDD and {2} vCPUs. '
                   'You need to remove some resources or add compute nodes '
                   'to have an ability to run this OSTF test.'
                   .format(self.min_required_ram_mb, 40, 2))
            LOG.debug(msg)
            self.skipTest(msg)

        if self.package_exists(self.dummy_fqdn):
            package = self.get_package_by_fqdn(self.dummy_fqdn)
            self.delete_package(package["id"])

        fail_msg = ("Package preparation failed. Please refer to "
                    "OSTF logs for more information")
        zip_path = self.verify(10, self.zip_dir, 1, fail_msg,
                               'prepare package',
                               os.path.dirname(__file__), self.dummy_fqdn)

        fail_msg = ("Package uploading failed. "
                    "Please refer to Openstack and OSTF logs")
        self.package = self.verify(10, self.upload_package, 2, fail_msg,
                                   'uploading package', 'SimpleApp',
                                   {"categories": ["Web"], "tags": ["tag"]},
                                   zip_path)

        fail_msg = "Can't create environment. Murano API is not available. "
        self.environment = self.verify(15, self.create_environment,
                                       3, fail_msg, 'creating environment',
                                       self.env_name)

        fail_msg = "User can't create session for environment. "
        session = self.verify(5, self.create_session,
                              4, fail_msg, "session creating",
                              self.environment.id)

        post_body = {
            "instance": {
                "flavor": self.flavor_name,
                "image": "TestVM",
                "assignFloatingIp": True,
                "?": {
                    "type": "io.murano.resources.LinuxMuranoInstance",
                    "id": str(uuid.uuid4())
                },
                "name": rand_name("testMurano")
            },
            "name": rand_name("teMurano"),
            "?": {
                "_{id}".format(id=uuid.uuid4().hex): {
                    "name": "SimpleApp"
                },
                "type": self.dummy_fqdn,
                "id": str(uuid.uuid4())
            }
        }

        fail_msg = "User can't create service. "
        self.verify(5, self.create_service,
                    5, fail_msg, "service creating",
                    self.environment.id, session.id, post_body)

        fail_msg = "User can't deploy session. "
        self.verify(5, self.deploy_session,
                    6, fail_msg,
                    "sending session on deployment",
                    self.environment.id, session.id)

        fail_msg = "Deployment was not completed correctly. "
        self.verify(860, self.deploy_check,
                    7, fail_msg, 'deployment is going',
                    self.environment)

        self.verify(5, self.deployments_status_check, 8, fail_msg,
                    'Check deployments status',
                    self.environment.id)

        fail_msg = "Can't delete environment. "
        self.verify(60, self.environment_delete_check,
                    9, fail_msg, "deleting environment",
                    self.environment.id)

        fail_msg = "Can't delete package"
        self.verify(5, self.delete_package, 10, fail_msg, "deleting_package",
                    self.package.id)

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
            7. Checking ports
            8. Send request to delete environment.

        Duration: 2140 s.
        Deployment tags: Murano, Heat
        Available since release: 2014.2-6.0
        """

        vms_count = self.get_info_about_available_resources(
            self.min_required_ram_mb, 40, 2)
        if vms_count < 1:
            msg = ('This test requires more hardware resources of your '
                   'OpenStack cluster: your cloud should allow to create '
                   'at least 1 VM with {0} MB of RAM, {1} HDD and {2} vCPUs. '
                   'You need to remove some resources or add compute nodes '
                   'to have an ability to run this OSTF test.'
                   .format(self.min_required_ram_mb, 40, 2))
            LOG.debug(msg)
            self.skipTest(msg)

        if not self.image:
            msg = ('Murano image was not properly registered or was not '
                   'uploaded at all. Please refer to the Fuel '
                   'documentation ({0}) to find out how to upload and/or '
                   'register image for Murano.'.format(self.doc_link))
            LOG.debug(msg)
            self.skipTest(msg)

        if not self.package_exists('io.murano.apps.apache.ApacheHttpServer'):
            self.skipTest("This test requires Apache HTTP Server application."
                          "Please add this application to Murano "
                          "and run this test again.")

        fail_msg = "Can't create environment. Murano API is not available. "
        self.environment = self.verify(15, self.create_environment,
                                       1, fail_msg, 'creating environment',
                                       self.env_name)

        fail_msg = "User can't create session for environment. "
        session = self.verify(5, self.create_session,
                              2, fail_msg, "session creating",
                              self.environment.id)

        post_body = {
            "instance": {
                "flavor": self.flavor_name,
                "image": self.image.name,
                "assignFloatingIp": True,
                "?": {
                    "type": "io.murano.resources.LinuxMuranoInstance",
                    "id": str(uuid.uuid4())
                },
                "name": rand_name("testMurano")
            },
            "name": rand_name("teMurano"),
            "?": {
                "_{id}".format(id=uuid.uuid4().hex): {
                    "name": "Apache"
                },
                "type": "io.murano.apps.apache.ApacheHttpServer",
                "id": str(uuid.uuid4())
            }
        }

        fail_msg = "User can't create service. "
        apache = self.verify(5, self.create_service,
                             3, fail_msg, "service creating",
                             self.environment.id, session.id, post_body)

        fail_msg = "User can't deploy session. "
        self.verify(5, self.deploy_session,
                    4, fail_msg,
                    "sending session on deployment",
                    self.environment.id, session.id)

        fail_msg = "Deployment was not completed correctly. "
        self.environment = self.verify(1800, self.deploy_check,
                                       5, fail_msg, 'deployment is going',
                                       self.environment)

        self.verify(5, self.deployments_status_check,
                    6, fail_msg,
                    'Check deployments status',
                    self.environment.id)

        self.verify(300, self.port_status_check,
                    7, fail_msg,
                    'Check that needed ports are opened',
                    self.environment, [[apache['instance']['name'], 22, 80]])

        fail_msg = "Can't delete environment. "
        self.verify(5, self.delete_environment,
                    8, fail_msg, "deleting environment",
                    self.environment.id)

    def test_deploy_wordpress_app(self):
        """Check that user can deploy WordPress app in Murano environment
        Target component: Murano

        Scenario:
            1. Send request to create environment.
            2. Send request to create session for environment.
            3. Send request to create MySQL.
            4. Send request to create Linux-based service Apache.
            5. Send request to create WordPress.
            6. Request to deploy session.
            7. Checking environment status.
            8. Checking deployments status.
            9. Checking ports availability.
            10. Checking WordPress path.
            11. Send request to delete environment.

        Duration: 2140 s.
        Deployment tags: Murano, Heat
        Available since release: 2014.2-6.1
        """

        vms_count = self.get_info_about_available_resources(
            self.min_required_ram_mb, 40, 2)
        if vms_count < 2:
            msg = ('This test requires more hardware resources of your '
                   'OpenStack cluster: your cloud should allow to create '
                   'at least 2 VMs with {0} MB of RAM, {1} HDD and {2} vCPUs.'
                   ' You need to remove some resources or add compute nodes '
                   'to have an ability to run this OSTF test.'
                   .format(self.min_required_ram_mb, 40, 2))
            LOG.debug(msg)
            self.skipTest(msg)

        if not self.image:
            msg = ('Murano image was not properly registered or was not '
                   'uploaded at all. Please refer to the Fuel '
                   'documentation ({0}) to find out how to upload and/or '
                   'register image for Murano.'.format(self.doc_link))
            LOG.debug(msg)
            self.skipTest(msg)

        if not self.package_exists('io.murano.apps.apache.ApacheHttpServer',
                                   'io.murano.databases.MySql',
                                   'io.murano.apps.WordPress'):
            self.skipTest("This test requires Apache HTTP Server, "
                          "MySQL database and WordPress applications."
                          "Please add this applications to Murano and "
                          "run this test again.")

        fail_msg = "Can't create environment. Murano API is not available. "
        self.environment = self.verify(15, self.create_environment,
                                       1, fail_msg, 'creating environment',
                                       self.env_name)

        fail_msg = "User can't create session for environment. "
        session = self.verify(5, self.create_session,
                              2, fail_msg, "session creating",
                              self.environment.id)

        post_body = {
            "instance": {
                "flavor": self.flavor_name,
                "image": self.image.name,
                "assignFloatingIp": True,
                "?": {
                    "type": "io.murano.resources.LinuxMuranoInstance",
                    "id": str(uuid.uuid4())
                },
                "name": rand_name("testMurano")
            },
            "name": rand_name("teMurano"),
            "database": rand_name("ostf"),
            "username": rand_name("ostf"),
            "password": rand_name("Ost1@"),
            "?": {
                "_{id}".format(id=uuid.uuid4().hex): {
                    "name": "MySQL"
                },
                "type": "io.murano.databases.MySql",
                "id": str(uuid.uuid4())
            }
        }

        fail_msg = "User can't create service MySQL. "
        self.mysql = self.verify(5, self.create_service,
                                 3, fail_msg, "service creating",
                                 self.environment.id, session.id,
                                 post_body)

        post_body = {
            "instance": {
                "flavor": self.flavor_name,
                "image": self.image.name,
                "assignFloatingIp": True,
                "?": {
                    "type": "io.murano.resources.LinuxMuranoInstance",
                    "id": str(uuid.uuid4())
                },
                "name": rand_name("testMurano")
            },
            "name": rand_name("teMurano"),
            "enablePHP": True,
            "?": {
                "_{id}".format(id=uuid.uuid4().hex): {
                    "name": "Apache"
                },
                "type": "io.murano.apps.apache.ApacheHttpServer",
                "id": str(uuid.uuid4())
            }
        }

        fail_msg = "User can't create service Apache. "
        self.apache = self.verify(5, self.create_service,
                                  4, fail_msg, "service creating",
                                  self.environment.id, session.id,
                                  post_body)

        post_body = {
            "name": rand_name("teMurano"),
            "server": self.apache,
            "database": self.mysql,
            "dbName": "wordpress",
            "dbUser": "wp_user",
            "dbPassword": "U0yleh@c",
            "?": {
                "_{id}".format(id=uuid.uuid4().hex): {
                    "name": "WordPress"
                },
                "type": "io.murano.apps.WordPress",
                "id": str(uuid.uuid4())
            }
        }

        fail_msg = "User can't create service WordPress. "
        self.verify(5, self.create_service,
                    5, fail_msg, "service creating",
                    self.environment.id, session.id, post_body)

        fail_msg = "User can't deploy session. "
        self.verify(5, self.deploy_session,
                    6, fail_msg,
                    "sending session on deployment",
                    self.environment.id, session.id)

        fail_msg = "Deployment was not completed correctly. "
        self.environment = self.verify(2400, self.deploy_check,
                                       7, fail_msg, 'deployment is going',
                                       self.environment)

        self.verify(5, self.deployments_status_check,
                    8, fail_msg,
                    'Check deployments status',
                    self.environment.id)

        self.verify(300, self.port_status_check,
                    9, fail_msg,
                    'Check that needed ports are opened',
                    self.environment,
                    [[self.apache['instance']['name'], 22, 80],
                     [self.mysql['instance']['name'], 22, 3306]])

        fail_msg = "Path to WordPress unavailable"
        self.verify(30, self.check_path, 10, fail_msg,
                    'checking path availability',
                    self.environment, "wordpress",
                    self.apache['instance']['name'])

        fail_msg = "Can't delete environment. "
        self.verify(10, self.delete_environment,
                    11, fail_msg, "deleting environment",
                    self.environment.id)
