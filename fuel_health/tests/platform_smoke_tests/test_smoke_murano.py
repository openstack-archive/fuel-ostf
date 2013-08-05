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
        2. Key Pair 'murano-lb-key'
        3. Internet access for virtual machines in OpenStack
        4. Windows image with metadata should be imported.
             Example Metadata for Windows image in Glance:
             murano_image_info = {"type":"ws-2012-std",
                                  "title":"Windows Server 2012"}
    """

    def check_image():
        fail_msg = "Windows image 'ws-2012-std' with Murano tag wasn't" + \
                   " imported into Glance"

        find_image = lambda k: len(
            [i for i in self.compute_client.images.list()
             if 'murano_image_info' in i.metadata and \
             'ws-2012-std' == i.name and \
             'ws-2012-std' == i.metadata[k]['type']]) > 0

        self.verify(5, find_image, 1, fail_msg,
                    "checking if Windows image with Murano tag is available",
                    'murano_image_info')

    def test_deploy_ad(self):
        """Murano environment with AD service deployment
        Test checks that user can deploy AD.
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

        Duration: 120 - 1830 s.

        Deployment tags: Murano, Heat
        """

        self.check_image()

        fail_msg = 'Cannot create environment.'
        self.environment = self.verify(5, self.create_environment,
                                       2, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = 'User can not create session for environment.'
        session = self.verify(5, self.create_session,
                              3, fail_msg, "session creating",
                              self.environment.id)

        post_body = {"type": "activeDirectory","name": "ad.local",
                    "adminPassword": "P@ssw0rd", "domain": "ad.local",
                    "availabilityZone": "nova", "unitNamingPattern": "",
                    "flavor": "m1.medium", "osImage":
                    {"type": "ws-2012-std", "name": "ws-2012-std", "title":
                    "Windows Server 2012 Standard"},"configuration":
                    "standalone", "units": [{"isMaster": True,
                    "recoveryPassword": "P@ssw0rd",
                    "location": "west-dc"}]}

        fail_msg = 'User can not create service.'
        service = self.verify(5, self.create_service,
                              4, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = 'User can not deploy session'
        deploy_sess = self.verify(10, self.deploy_session,
                                  5, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = 'Deploy did not complete correctly'
        status_env = self.verify(1800, self.deploy_check,
                                 6, fail_msg, 'deploy is going',
                                 self.environment.id)

        deployment_status = self.verify(40, self.deployments_status_check,
                                        7, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = 'Cannot delete environment.'
        self.verify(5, self.delete_environment,
                    8, fail_msg, "deleting environment",
                    self.environment.id)

    def test_deploy_iis(self):
        """Murano environment with IIS service deployment
        Test checks that user can deploy IIS.
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

        Duration: 120 - 1830 s.

        Deployment tags: Murano, Heat
        """

        self.check_image()

        fail_msg = 'Cannot create environment.'
        self.environment = self.verify(5, self.create_environment,
                                       2, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = 'User can not create session for environment.'
        session = self.verify(5, self.create_session,
                              3, fail_msg, "session creating",
                              self.environment.id)

        creds = {'username': 'Administrator',
                 'password': 'P@ssw0rd'}
        post_body = {"type": "webServer", "domain": "",
                     "availabilityZone": "nova", "name": "someIIS",
                     "adminPassword": "P@ssw0rd", "unitNamingPattern": "",
                     "osImage": {"type": "ws-2012-std",
                                 "name": "ws-2012-std",
                                 "title": "Windows Server 2012 Standard"},
                     "units": [{}], "credentials": creds,
                     "flavor": "m1.medium"}

        fail_msg = 'User can not create service.'
        service = self.verify(5, self.create_service,
                              4, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = 'User can not deploy session'
        deploy_sess = self.verify(10, self.deploy_session,
                                  5, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = 'Deploy did not complete correctly'
        status_env = self.verify(1800, self.deploy_check,
                                 6, fail_msg, 'deploy is going',
                                 self.environment.id)

        deployment_status = self.verify(40, self.deployments_status_check,
                                        7, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = 'Cannot delete environment.'
        self.verify(5, self.delete_environment,
                    8, fail_msg, "deleting environment",
                    self.environment.id)

    def test_deploy_aspnet(self):
        """Murano environment with ASP.NET application service deployment
        Test checks that user can deploy ASPNet.
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

        Duration: 120 - 1830 s.

        Deployment tags: Murano, Heat
        """

        self.check_image()

        fail_msg = 'Cannot create environment.'
        self.environment = self.verify(5, self.create_environment,
                                       2, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = 'User can not create session for environment.'
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
                     "osImage": {"type": "ws-2012-std", "name": "ws-2012-std",
                     "title": "Windows Server 2012 Standard"},
                     "units": [{}], "credentials": creds,
                     "flavor": "m1.medium"}

        fail_msg = 'User can not create service.'
        service = self.verify(5, self.create_service,
                              4, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = 'User can not deploy session'
        deploy_sess = self.verify(10, self.deploy_session,
                                  5, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = 'Deploy did not complete correctly, '
        fail_msg += 'please check that virtual machines have Internet access'
        status_env = self.verify(1800, self.deploy_check,
                                 6, fail_msg, 'deploy is going',
                                 self.environment.id)

        deployment_status = self.verify(40, self.deployments_status_check,
                                        7, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = 'Cannot delete environment.'
        self.verify(5, self.delete_environment,
                    8, fail_msg, "deleting environment",
                    self.environment.id)

    def test_deploy_iis_farm(self):
        """Murano environment with IIS Servers Farm service deployment
        Test checks that user can deploy IIS farm.
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

        Duration: 120 - 1830 s.

        Deployment tags: Murano, Heat
        """

        self.check_image()

        keyname = 'murano-lb-key'
        fail_msg = "Key Pair {0} does not exist. Please, add this key pair" + \
                   " manually"

        self.verify(5, self.is_keypair_available, 2, fail_msg.format(keyname),
                    "checking if %s keypair is available" % keyname,
                    keyname)

        fail_msg = 'Cannot create environment.'
        self.environment = self.verify(5, self.create_environment,
                                       3, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = 'User can not create session for environment.'
        session = self.verify(5, self.create_session,
                              4, fail_msg, "session creating",
                              self.environment.id)

        creds = {'username': 'Administrator',
                 'password': 'P@ssw0rd'}
        post_body = {"type": "webServerFarm", "domain": "",
                     "availabilityZone": "nova", "name": "someIISFARM",
                     "adminPassword": "P@ssw0rd", "loadBalancerPort": 80,
                     "unitNamingPattern": "",
                     "osImage": {"type": "ws-2012-std", "name": "ws-2012-std",
                     "title": "Windows Server 2012 Standard"},
                     "units": [{}, {}],
                     "credentials": creds, "flavor": "m1.medium"}

        fail_msg = 'User can not create service.'
        service = self.verify(5, self.create_service,
                              5, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = 'User can not deploy session'
        deploy_sess = self.verify(10, self.deploy_session,
                                  6, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = 'Deploy did not complete correctly, '
        fail_msg += 'please check that Key Pair "murano-lb-key" exists'
        status_env = self.verify(1800, self.deploy_check,
                                 7, fail_msg, 'deploy is going',
                                 self.environment.id)

        deployment_status = self.verify(40, self.deployments_status_check,
                                        8, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = 'Cannot delete environment.'
        self.verify(5, self.delete_environment,
                    9, fail_msg, "deleting environment",
                    self.environment.id)

    def test_deploy_aspnet_farm(self):
        """Murano environment with ASP.NET application service deployment
        Test checks that user can deploy ASPNet farm.
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

        Duration: 120 - 1830 s.

        Deployment tags: Murano, Heat
        """

        self.check_image()

        keyname = 'murano-lb-key'
        fail_msg = "Key Pair {0} does not exist. Please, add this key pair" + \
                   " manually"

        self.verify(5, self.is_keypair_available, 2, fail_msg.format(keyname),
                    "checking if %s keypair is available" % keyname,
                    keyname)

        fail_msg = 'Cannot create environment.'
        self.environment = self.verify(5, self.create_environment,
                                       3, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = 'User can not create session for environment.'
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
                     "osImage": {"type": "ws-2012-std", "name": "ws-2012-std",
                     "title": "Windows Server 2012 Standard"},
                     "units": [{}, {}],
                     "credentials": creds, "flavor": "m1.medium"}

        fail_msg = 'User can not create service.'
        service = self.verify(5, self.create_service,
                              5, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = 'User can not deploy session'
        deploy_sess = self.verify(10, self.deploy_session,
                                  6, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = 'Deploy did not complete correctly, '
        fail_msg += 'please check, that Key Pair "murano-lb-key" exists '
        fail_msg += 'and virtual machines have Internet access'
        status_env = self.verify(1800, self.deploy_check,
                                 7, fail_msg, 'deploy is going',
                                 self.environment.id)

        deployment_status = self.verify(40, self.deployments_status_check,
                                        8, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = 'Cannot delete environment.'
        self.verify(5, self.delete_environment,
                    9, fail_msg, "deleting environment",
                    self.environment.id)

    def test_deploy_sql(self):
        """Murano environment with SQL service deployment
        Test checks that user can deploy SQL.
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

        Duration: 120 - 1830 s.

        Deployment tags: Murano, Heat
        """

        self.check_image()

        fail_msg = 'Cannot create environment.'
        self.environment = self.verify(5, self.create_environment,
                                       2, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = 'User can not create session for environment.'
        session = self.verify(5, self.create_session,
                              3, fail_msg, "session creating",
                              self.environment.id)

        post_body = {"type": "msSqlServer", "domain": "",
                     "availabilityZone": "nova", "name": "SQLSERVER",
                     "adminPassword": "P@ssw0rd", "unitNamingPattern": "",
                     "saPassword": "P@ssw0rd", "mixedModeAuth": "true",
                     "osImage": {"type": "ws-2012-std", "name": "ws-2012-std",
                     "title": "Windows Server 2012 Standard"},"units": [{}],
                     "credentials": {"username": "Administrator",
                     "password": "P@ssw0rd"}, "flavor": "m1.medium"}

        fail_msg = 'User can not create service.'
        service = self.verify(5, self.create_service,
                              4, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = 'User can not deploy session'
        deploy_sess = self.verify(10, self.deploy_session,
                                  5, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = 'Deploy did not complete correctly'
        status_env = self.verify(1800, self.deploy_check,
                                 6, fail_msg, 'deploy is going',
                                 self.environment.id)

        deployment_status = self.verify(40, self.deployments_status_check,
                                        7, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = 'Cannot delete environment.'
        self.verify(5, self.delete_environment,
                    8, fail_msg, "deleting environment",
                    self.environment.id)

    def test_deploy_sql_cluster(self):
        """Murano environment with SQL Cluster service deployment
        Test checks that user can deploy SQL Cluster.
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

        Duration: 200 - 2200 s.

        Deployment tags: Murano, Heat
        """

        self.check_image()

        fail_msg = 'Cannot create environment.'
        self.environment = self.verify(5, self.create_environment,
                                       2, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = 'User can not create session for environment.'
        session = self.verify(5, self.create_session,
                              3, fail_msg, "session creating",
                              self.environment.id)

        post_body = {"type": "activeDirectory","name": "ad.local",
                     "adminPassword": "P@ssw0rd", "domain": "ad.local",
                     "availabilityZone": "nova", "unitNamingPattern": "",
                     "flavor": "m1.medium", "osImage":
                     {"type": "ws-2012-std", "name": "ws-2012-std", "title":
                     "Windows Server 2012 Standard"},"configuration":
                     "standalone", "units": [{"isMaster": True,
                     "recoveryPassword": "P@ssw0rd",
                     "location": "west-dc"}]}

        fail_msg = 'User can not create service.'
        service = self.verify(5, self.create_service,
                              4, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = 'User can not deploy session'
        deploy_sess = self.verify(10, self.deploy_session,
                                  5, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = 'Deploy did not complete correctly'
        status_env = self.verify(1800, self.deploy_check,
                                 6, fail_msg, 'deploy is going',
                                 self.environment.id)

        deployment_status = self.verify(40, self.deployments_status_check,
                                        7, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = 'User can not create session for environment.'
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
                     "osImage": {"type": "ws-2012-std", "name": "ws-2012-std",
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
                     "unitNamingPattern": "", "units": [{"isMaster": True,
                     "name": "node1", "isSync": True}, {"isMaster": False,
                     "name": "node2", "isSync": True}],
                     "name": "Sqlname", "saPassword": "P@ssw0rd",
                     "databases": ['murano', 'test']}

        fail_msg = 'User can not create service.'
        service = self.verify(5, self.create_service,
                              9, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = 'User can not deploy session'
        deploy_sess = self.verify(10, self.deploy_session,
                                  10, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = 'Deploy did not complete correctly'
        status_env = self.verify(1800, self.deploy_check,
                                 11, fail_msg, 'deploy is going',
                                 self.environment.id)

        deployment_status = self.verify(40, self.deployments_status_check,
                                        12, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = 'Cannot delete environment.'
        self.verify(5, self.delete_environment,
                    13, fail_msg, "deleting environment",
                    self.environment.id)
