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


class MuranoDeploymentSmokeTests(murano.MuranoTest):
    """
    TestClass contains verifications of full Murano functionality.
    Special requirements:
        1. Murano component should be installed.
        2. Key Pair 'murano-lb-key'.
        3. Internet access for virtual machines in OpenStack.
        4. Windows image with Murano metadata should be imported.
    """

    def setUpClass(self):
        super(MuranoDeploymentSmokeTests, self).setUpClass()
        self.image = self.find_murano_image()

    def test_deploy_ad(self):
        """Check that user can deploy AD service in Murano environment
        Target component: Murano

        Scenario:
            1. Check Windows Server 2012 image in glance.
            2. Send request to create environment.
            3. Send request to create session for environment.
            4. Send request to create service AD.
            5. Request to deploy session.
            6. Checking environment status.
            7. Checking deployments status
            8. Send request to delete environment.

        Duration: 1830 s.

        Deployment tags: Murano, Heat
        """

        fail_msg = ("Step 1 failed: Windows Server 2012 image with Murano "
                    "tag isn't available. Need to import this image into "
                    "glance and mark with Murano metadata tag. Please "
                    "refer to the Fuel Web and Murano user documentation. ")
        self.verify_response_true(self.image, fail_msg)

        fail_msg = "Can't create environment. Murano API is not available. "
        self.environment = self.verify(5, self.create_environment,
                                       2, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = "User can't create session for environment. "
        session = self.verify(5, self.create_session,
                              3, fail_msg, "session creating",
                              self.environment.id)

        post_body = {"type": "activeDirectory", "name": "ad.local",
                     "adminPassword": "P@ssw0rd", "domain": "ad.local",
                     "availabilityZone": "nova", "unitNamingPattern": "",
                     "flavor": "m1.medium", "osImage":
                     {"type": "ws-2012-std", "name": str(self.image.name),
                      "title": "Windows Server 2012 Standard"},
                     "configuration": "standalone",
                     "units": [{"isMaster": True,
                                "recoveryPassword": "P@ssw0rd",
                                "location": "west-dc"}]}

        fail_msg = "User can't create service. "
        service = self.verify(5, self.create_service,
                              4, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = "User can't deploy session. "
        deploy_sess = self.verify(5, self.deploy_session,
                                  5, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = "Deploy did not complete correctly. "
        status_env = self.verify(1800, self.deploy_check,
                                 6, fail_msg, 'deploy is going',
                                 self.environment.id)

        deployment_status = self.verify(5, self.deployments_status_check,
                                        7, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = "Can't delete environment. "
        self.verify(5, self.delete_environment,
                    8, fail_msg, "deleting environment",
                    self.environment.id)

    def test_deploy_iis(self):
        """Check that user can deploy IIS in Murano environment
        Target component: Murano

        Scenario:
            1. Check Windows Server 2012 image in glance.
            2. Send request to create environment.
            3. Send request to create session for environment.
            4. Send request to create service IIS.
            5. Request to deploy session.
            6. Checking environment status.
            7. Checking deployments status
            8. Send request to delete environment.

        Duration: 1830 s.

        Deployment tags: Murano, Heat
        """

        fail_msg = ("Step 1 failed: Windows Server 2012 image with Murano "
                    "tag isn't available. Need to import this image into "
                    "glance and mark with Murano metadata tag. Please "
                    "refer to the Fuel Web and Murano user documentation. ")
        self.verify_response_true(self.image, fail_msg)

        fail_msg = "Can't create environment. Murano API is not available. "
        self.environment = self.verify(5, self.create_environment,
                                       2, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = "User can't create session for environment. "
        session = self.verify(5, self.create_session,
                              3, fail_msg, "session creating",
                              self.environment.id)

        creds = {'username': 'Administrator',
                 'password': 'P@ssw0rd'}
        post_body = {"type": "webServer", "domain": "",
                     "availabilityZone": "nova", "name": "someIIS",
                     "adminPassword": "P@ssw0rd", "unitNamingPattern": "",
                     "osImage": {"type": "ws-2012-std",
                                 "name": str(self.image.name),
                                 "title": "Windows Server 2012 Standard"},
                     "units": [{}], "credentials": creds,
                     "flavor": "m1.medium"}

        fail_msg = "User can't create service. "
        service = self.verify(5, self.create_service,
                              4, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = "User can't deploy session. "
        deploy_sess = self.verify(5, self.deploy_session,
                                  5, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = "Deploy did not complete correctly. "
        status_env = self.verify(1800, self.deploy_check,
                                 6, fail_msg, 'deploy is going',
                                 self.environment.id)

        deployment_status = self.verify(5, self.deployments_status_check,
                                        7, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = "Can't delete environment. "
        self.verify(5, self.delete_environment,
                    8, fail_msg, "deleting environment",
                    self.environment.id)

    def test_deploy_aspnet(self):
        """Check that user can deploy ASP.NET in Murano environment
        Target component: Murano

        Special requirements:
            1. Internet access for virtual machines in OpenStack

        Scenario:
            1. Check Windows Server 2012 image in glance.
            2. Send request to create environment.
            3. Send request to create session for environment.
            4. Send request to create service ASPNet.
            5. Request to deploy session.
            6. Checking environment status.
            7. Checking deployments status
            8. Send request to delete environment.

        Duration: 1830 s.

        Deployment tags: Murano, Heat
        """

        fail_msg = ("Step 1 failed: Windows Server 2012 image with Murano "
                    "tag isn't available. Need to import this image into "
                    "glance and mark with Murano metadata tag. Please "
                    "refer to the Fuel Web and Murano user documentation. ")
        self.verify_response_true(self.image, fail_msg)

        fail_msg = "Can't create environment. Murano API is not available. "
        self.environment = self.verify(5, self.create_environment,
                                       2, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = "User can't create session for environment. "
        session = self.verify(5, self.create_session,
                              3, fail_msg, "session creating",
                              self.environment.id)

        creds = {'username': 'Administrator',
                 'password': 'P@ssw0rd'}
        asp_repository = "git://github.com/Mirantis/murano-mvc-demo.git"
        post_body = {"type": "aspNetApp", "domain": "",
                     "availabilityZone": "nova", "name": "someasp",
                     "repository": asp_repository,
                     "adminPassword": "P@ssw0rd", "unitNamingPattern": "",
                     "osImage":
                     {"type": "ws-2012-std", "name": str(self.image.name),
                      "title": "Windows Server 2012 Standard"},
                     "units": [{}], "credentials": creds,
                     "flavor": "m1.medium"}

        fail_msg = "User can't create service. "
        service = self.verify(5, self.create_service,
                              4, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = "User can't deploy session. "
        deploy_sess = self.verify(5, self.deploy_session,
                                  5, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = ("Deploy did not complete correctly, please check that "
                    "virtual machines have Internet access. ")
        status_env = self.verify(1800, self.deploy_check,
                                 6, fail_msg, 'deploy is going',
                                 self.environment.id)

        deployment_status = self.verify(5, self.deployments_status_check,
                                        7, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = "Can't delete environment. "
        self.verify(5, self.delete_environment,
                    8, fail_msg, "deleting environment",
                    self.environment.id)

    def test_deploy_iis_farm(self):
        """Check user can deploy IIS farm in Murano environment
        Target component: Murano

        Special requirements:
            1. Key Pair 'murano-lb-key'

        Scenario:
            1. Check Windows Server 2012 image in glance.
            2. Check that Key Pair 'murano-lb-key' exists.
            3. Send request to create environment.
            4. Send request to create session for environment.
            5. Send request to create service IIS farm.
            6. Request to deploy session.
            7. Checking environment status.
            8. Checking deployments status
            9. Send request to delete environment.

        Duration: 1830 s.

        Deployment tags: Murano, Heat
        """

        fail_msg = ("Step 1 failed: Windows Server 2012 image with Murano "
                    "tag isn't available. Need to import this image into "
                    "glance and mark with Murano metadata tag. Please "
                    "refer to the Fuel Web and Murano user documentation. ")
        self.verify_response_true(self.image, fail_msg)

        fail_msg = ("Step 2 failed: Key Pair 'murano-lb-key' does not exist."
                    " Please, add this key pair manually. ")
        self.verify_response_true(self.find_keypair('murano-lb-key'),
                                  fail_msg)

        fail_msg = "Can't create environment. Murano API is not available. "
        self.environment = self.verify(5, self.create_environment,
                                       3, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = "User can't create session for environment. "
        session = self.verify(5, self.create_session,
                              4, fail_msg, "session creating",
                              self.environment.id)

        creds = {'username': 'Administrator',
                 'password': 'P@ssw0rd'}
        post_body = {"type": "webServerFarm", "domain": "",
                     "availabilityZone": "nova", "name": "someIISFARM",
                     "adminPassword": "P@ssw0rd", "loadBalancerPort": 80,
                     "unitNamingPattern": "",
                     "osImage":
                     {"type": "ws-2012-std", "name": str(self.image.name),
                      "title": "Windows Server 2012 Standard"},
                     "units": [{}, {}],
                     "credentials": creds, "flavor": "m1.medium"}

        fail_msg = "User can't create service. "
        service = self.verify(5, self.create_service,
                              5, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = "User can't deploy session. "
        deploy_sess = self.verify(5, self.deploy_session,
                                  6, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = ("Deploy did not complete correctly, "
                    "please check that Key Pair 'murano-lb-key' exists. ")
        status_env = self.verify(1800, self.deploy_check,
                                 7, fail_msg, 'deploy is going',
                                 self.environment.id)

        deployment_status = self.verify(5, self.deployments_status_check,
                                        8, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = "Can't delete environment. "
        self.verify(5, self.delete_environment,
                    9, fail_msg, "deleting environment",
                    self.environment.id)

    def test_deploy_aspnet_farm(self):
        """Check that user can deploy ASP.NET farm in Murano environment
        Target component: Murano

        Special requirements:
            1. Key Pair 'murano-lb-key'
            2. Internet access for virtual machines in OpenStack

        Scenario:
            1. Check Windows Server 2012 image in glance.
            2. Check that Key Pair 'murano-lb-key' exists.
            3. Send request to create environment.
            4. Send request to create session for environment.
            5. Send request to create service ASPNet farm.
            6. Request to deploy session.
            7. Checking environment status.
            8. Checking deployments status
            9. Send request to delete environment.

        Duration: 1830 s.

        Deployment tags: Murano, Heat
        """

        fail_msg = ("Step 1 failed: Windows Server 2012 image with Murano "
                    "tag isn't available. Need to import this image into "
                    "glance and mark with Murano metadata tag. Please "
                    "refer to the Fuel Web and Murano user documentation. ")
        self.verify_response_true(self.image, fail_msg)

        fail_msg = ("Step 2 failed: Key Pair 'murano-lb-key' does not exist."
                    " Please, add this key pair manually. ")
        self.verify_response_true(self.find_keypair('murano-lb-key'),
                                  fail_msg)

        fail_msg = "Can't create environment. Murano API is not available. "
        self.environment = self.verify(5, self.create_environment,
                                       3, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = "User can't create session for environment. "
        session = self.verify(5, self.create_session,
                              4, fail_msg, "session creating",
                              self.environment.id)

        creds = {'username': 'Administrator',
                 'password': 'P@ssw0rd'}
        asp_repository = "git://github.com/Mirantis/murano-mvc-demo.git"
        post_body = {"type": "aspNetAppFarm", "domain": "",
                     "availabilityZone": "nova", "name": "SomeApsFarm",
                     "repository": asp_repository,
                     "adminPassword": "P@ssw0rd", "loadBalancerPort": 80,
                     "unitNamingPattern": "",
                     "osImage":
                     {"type": "ws-2012-std", "name": str(self.image.name),
                      "title": "Windows Server 2012 Standard"},
                     "units": [{}, {}],
                     "credentials": creds, "flavor": "m1.medium"}

        fail_msg = "User can't create service. "
        service = self.verify(5, self.create_service,
                              5, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = "User can't deploy session. "
        deploy_sess = self.verify(5, self.deploy_session,
                                  6, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = ("Deploy did not complete correctly, "
                    "please check, that Key Pair 'murano-lb-key' exists "
                    "and virtual machines have Internet access. ")
        status_env = self.verify(1800, self.deploy_check,
                                 7, fail_msg, 'deploy is going',
                                 self.environment.id)

        deployment_status = self.verify(5, self.deployments_status_check,
                                        8, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = "Can't delete environment. "
        self.verify(5, self.delete_environment,
                    9, fail_msg, "deleting environment",
                    self.environment.id)

    def test_deploy_sql(self):
        """Check that user can deploy SQL in Murano environment
        Target component: Murano

        Scenario:
            1. Check Windows Server 2012 image in glance.
            2. Send request to create environment.
            3. Send request to create session for environment.
            4. Send request to create service SQL.
            5. Request to deploy session.
            6. Checking environment status.
            7. Checking deployments status
            8. Send request to delete environment.

        Duration: 1830 s.

        Deployment tags: Murano, Heat
        """

        fail_msg = ("Step 1 failed: Windows Server 2012 image with Murano "
                    "tag isn't available. Need to import this image into "
                    "glance and mark with Murano metadata tag. Please "
                    "refer to the Fuel Web and Murano user documentation. ")
        self.verify_response_true(self.image, fail_msg)

        fail_msg = "Can't create environment. Murano API is not available. "
        self.environment = self.verify(5, self.create_environment,
                                       2, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = "User can't create session for environment. "
        session = self.verify(5, self.create_session,
                              3, fail_msg, "session creating",
                              self.environment.id)

        post_body = {"type": "msSqlServer", "domain": "",
                     "availabilityZone": "nova", "name": "SQLSERVER",
                     "adminPassword": "P@ssw0rd", "unitNamingPattern": "",
                     "saPassword": "P@ssw0rd", "mixedModeAuth": "true",
                     "osImage":
                     {"type": "ws-2012-std", "name": str(self.image.name),
                      "title": "Windows Server 2012 Standard"}, "units": [{}],
                     "credentials": {"username": "Administrator",
                                     "password": "P@ssw0rd"},
                     "flavor": "m1.medium"}

        fail_msg = "User can't create service. "
        service = self.verify(5, self.create_service,
                              4, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = "User can't deploy session. "
        deploy_sess = self.verify(5, self.deploy_session,
                                  5, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = "Deploy did not complete correctly. "
        status_env = self.verify(1800, self.deploy_check,
                                 6, fail_msg, 'deploy is going',
                                 self.environment.id)

        deployment_status = self.verify(5, self.deployments_status_check,
                                        7, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = "Can't delete environment. "
        self.verify(5, self.delete_environment,
                    8, fail_msg, "deleting environment",
                    self.environment.id)

    def test_deploy_sql_cluster(self):
        """Check that user can deploy SQL Cluster in Murano environment
        Target component: Murano

        Scenario:
            1. Check Windows Server 2012 image in glance.
            2. Send request to create environment.
            3. Send request to create session for environment.
            4. Send request to create service AD.
            5. Request to deploy session.
            6. Checking environment status.
            7. Checking deployments status.
            8. Send request to create session for environment.
            9. Send request to create service SQL cluster.
            10. Request to deploy session..
            11. Checking environment status.
            12. Checking deployments status.
            13. Send request to delete environment.

        Duration: 2200 s.

        Deployment tags: Murano, Heat
        """

        fail_msg = ("Step 1 failed: Windows Server 2012 image with Murano "
                    "tag isn't available. Need to import this image into "
                    "glance and mark with Murano metadata tag. Please "
                    "refer to the Fuel Web and Murano user documentation. ")
        self.verify_response_true(self.image, fail_msg)

        fail_msg = "Can't create environment. Murano API is not available. "
        self.environment = self.verify(5, self.create_environment,
                                       2, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = "User can't create session for environment. "
        session = self.verify(5, self.create_session,
                              3, fail_msg, "session creating",
                              self.environment.id)

        post_body = {"type": "activeDirectory", "name": "ad.local",
                     "adminPassword": "P@ssw0rd", "domain": "ad.local",
                     "availabilityZone": "nova", "unitNamingPattern": "",
                     "flavor": "m1.medium", "osImage":
                     {"type": "ws-2012-std", "name": str(self.image.name),
                      "title": "Windows Server 2012 Standard"},
                     "configuration": "standalone",
                     "units": [{"isMaster": True,
                                "recoveryPassword": "P@ssw0rd",
                                "location": "west-dc"}]}

        fail_msg = "User can't create service. "
        service = self.verify(5, self.create_service,
                              4, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = "User can't deploy session. "
        deploy_sess = self.verify(5, self.deploy_session,
                                  5, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = "Deploy did not complete correctly. "
        status_env = self.verify(1800, self.deploy_check,
                                 6, fail_msg, 'deploy is going',
                                 self.environment.id)

        deployment_status = self.verify(5, self.deployments_status_check,
                                        7, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = "User can't create session for environment. "
        session = self.verify(5, self.create_session,
                              8, fail_msg, "session creating",
                              self.environment.id)

        # it is just 'any unused IP addresses'
        AG = self.config.murano.agListnerIP
        clIP = self.config.murano.clusterIP

        post_body = {"domain": "ad.local", "domainAdminPassword": "P@ssw0rd",
                     "externalAD": False,
                     "sqlServiceUserName": "Administrator",
                     "sqlServicePassword": "P@ssw0rd",
                     "osImage":
                     {"type": "ws-2012-std", "name": str(self.image.name),
                      "title": "Windows Server 2012 Standard"},
                     "agListenerName": "SomeSQL_AGListner",
                     "flavor": "m1.medium",
                     "agGroupName": "SomeSQL_AG",
                     "domainAdminUserName": "Administrator",
                     "agListenerIP": AG,
                     "clusterIP": clIP,
                     "type": "msSqlClusterServer", "availabilityZone": "nova",
                     "adminPassword": "P@ssw0rd",
                     "clusterName": "SomeSQL", "mixedModeAuth": True,
                     "unitNamingPattern": "", "units":
                     [{"isMaster": True, "name": "node1", "isSync": True},
                      {"isMaster": False, "name": "node2", "isSync": True}],
                     "name": "Sqlname", "saPassword": "P@ssw0rd",
                     "databases": ['murano', 'test']}

        fail_msg = "User can't create service. "
        service = self.verify(5, self.create_service,
                              9, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = "User can't deploy session. "
        deploy_sess = self.verify(5, self.deploy_session,
                                  10, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = "Deploy did not complete correctly. "
        status_env = self.verify(1800, self.deploy_check,
                                 11, fail_msg, 'deploy is going',
                                 self.environment.id)

        deployment_status = self.verify(5, self.deployments_status_check,
                                        12, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = "Can't delete environment. "
        self.verify(5, self.delete_environment,
                    13, fail_msg, "deleting environment",
                    self.environment.id)
