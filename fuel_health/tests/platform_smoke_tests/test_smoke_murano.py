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
        2. Windows image with metadata should be imported.
    """

    def test_check_default_key_pair(self):
        """Check Default Key Pair 'murano-lb-key' For Server Farms
        Test checks that user has Key Pair 'murano-lb-key'.
        Please, see more detailed information in Murano Administrator Guide.
        Target component: Murano

        Scenario:
            1. Check that Key Pair 'murano-lb-key' exists.
        Duration: 5 s.
        """

        keyname = 'murano-lb-key'
        fail_msg = "Key Pair %s does not exist. " % keyname

        self.verify(5, self.is_keypair_available, 1, fail_msg,
                    "checking if %s keypair is available" % keyname,
                    keyname)

    def test_check_windows_image_with_murano_tag(self):
        """Check Windows Image With Murano Tag
        Test checks that user has windows image with murano tag.
        Please, see more detailed information in Murano Administrator Guide.
        Target component: Murano

        Scenario:
            1. Check that Windows image with Murano tag imported in Glance.
        Duration: 5 s.
        """

        exp_key = 'murano_image_info'
        exp_value = '{"type":"ws-2012-std","title":"Windows Server 2012"}'

        fail_msg = "Windows image with Murano tag wasn't imported into Glance"

        find_image = lambda k, v: len(
            [i for i in self.compute_client.images.list()
             if k in i.metadata and v == i.metadata[k]]) > 0

        self.verify(5, find_image, 1, fail_msg,
                    "checking if Windows image with Murano tag is available",
                    exp_key, exp_value)

    def test_deploy_ad(self):
        """Check Murano API Service: Deploy AD
        Test checks that user can deploy AD.
        Target component: Murano

        Scenario:
            1. Send request to create environment.
            2. Send request to create session for environment.
            3. Send request to create service AD.
            4. Request to deploy session.
            5. Checking environment status.
            6. Checking deployments status
            7. Send request to delete environment.
        Duration: 120 - 1830 s.
        """

        fail_msg = 'Cannot create environment.'
        self.environment = self.verify(5, self.create_environment,
                                       1, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = 'User can not create session for environment.'
        session = self.verify(5, self.create_session,
                              2, fail_msg, "session creating",
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
                              3, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = 'User can not deploy session'
        deploy_sess = self.verify(10, self.deploy_session,
                                  4, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = 'Deploy did not complete correctly'
        status_env = self.verify(1800, self.deploy_check,
                                    5, fail_msg, 'deploy is going',
                                    self.environment.id)

        step = '6. Checking deployments status'
        deployment_status = self.verify(40, self.deployments_status_check,
                                        step, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = 'Cannot delete environment.'
        self.verify(5, self.delete_environment,
                    7, fail_msg, "deleting environment",
                    self.environment.id)

    def test_deploy_iis(self):
        """Check Murano API Service: Deploy IIS
        Test checks that user can deploy IIS.
        Target component: Murano

        Scenario:
            1. Send request to create environment.
            2. Send request to create session for environment.
            3. Send request to create service IIS.
            4. Request to deploy session.
            5. Checking environment status.
            6. Checking deployments status
            7. Send request to delete environment.
        Duration: 120 - 1830 s.
        """

        fail_msg = 'Cannot create environment.'
        self.environment = self.verify(5, self.create_environment,
                                       1, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = 'User can not create session for environment.'
        session = self.verify(5, self.create_session,
                              2, fail_msg, "session creating",
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
                              3, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = 'User can not deploy session'
        deploy_sess = self.verify(10, self.deploy_session,
                                  4, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = 'Deploy did not complete correctly'
        status_env = self.verify(1800, self.deploy_check,
                                    5, fail_msg, 'deploy is going',
                                    self.environment.id)

        step = '6. Checking deployments status'
        deployment_status = self.verify(40, self.deployments_status_check,
                                        step, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = 'Cannot delete environment.'
        self.verify(5, self.delete_environment,
                    7, fail_msg, "deleting environment",
                    self.environment.id)

    def test_deploy_aspnet(self):
        """Check Murano API Service: Deploy ASPNet
        Test checks that user can deploy ASPNet.
        Target component: Murano

        Scenario:
            1. Send request to create environment.
            2. Send request to create session for environment.
            3. Send request to create service ASPNet.
            4. Request to deploy session.
            5. Checking environment status.
            6. Checking deployments status
            7. Send request to delete environment.
        Duration: 120 - 1830 s.
        """

        fail_msg = 'Cannot create environment.'
        self.environment = self.verify(5, self.create_environment,
                                       1, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = 'User can not create session for environment.'
        session = self.verify(5, self.create_session,
                              2, fail_msg, "session creating",
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
                              3, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = 'User can not deploy session'
        deploy_sess = self.verify(10, self.deploy_session,
                                  4, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = 'Deploy did not complete correctly'
        status_env = self.verify(1800, self.deploy_check,
                                    5, fail_msg, 'deploy is going',
                                    self.environment.id)

        step = '6. Checking deployments status'
        deployment_status = self.verify(40, self.deployments_status_check,
                                        step, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = 'Cannot delete environment.'
        self.verify(5, self.delete_environment,
                    7, fail_msg, "deleting environment",
                    self.environment.id)

    def test_deploy_iis_farm(self):
        """Check Murano API Service: Deploy IIS farm
        Test checks that user can deploy IIS farm.
        Target component: Murano

        Scenario:
            1. Send request to create environment.
            2. Send request to create session for environment.
            3. Send request to create service IIS farm.
            4. Request to deploy session.
            5. Checking environment status.
            6. Checking deployments status
            7. Send request to delete environment.
        Duration: 120 - 1830 s.
        """

        fail_msg = 'Cannot create environment.'
        self.environment = self.verify(5, self.create_environment,
                                       1, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = 'User can not create session for environment.'
        session = self.verify(5, self.create_session,
                              2, fail_msg, "session creating",
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
                              3, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = 'User can not deploy session'
        deploy_sess = self.verify(10, self.deploy_session,
                                  4, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = 'Deploy did not complete correctly'
        status_env = self.verify(1800, self.deploy_check,
                                    5, fail_msg, 'deploy is going',
                                    self.environment.id)

        step = '6. Checking deployments status'
        deployment_status = self.verify(40, self.deployments_status_check,
                                        step, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = 'Cannot delete environment.'
        self.verify(5, self.delete_environment,
                    7, fail_msg, "deleting environment",
                    self.environment.id)

    def test_deploy_aspnet_farm(self):
        """Check Murano API Service: Deploy ASPNet farm
        Test checks that user can deploy ASPNet farm.
        Target component: Murano

        Scenario:
            1. Send request to create environment.
            2. Send request to create session for environment.
            3. Send request to create service ASPNet farm.
            4. Request to deploy session.
            5. Checking environment status.
            6. Checking deployments status
            7. Send request to delete environment.
        Duration: 120 - 1830 s.
        """

        fail_msg = 'Cannot create environment.'
        self.environment = self.verify(5, self.create_environment,
                                       1, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = 'User can not create session for environment.'
        session = self.verify(5, self.create_session,
                              2, fail_msg, "session creating",
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
                              3, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = 'User can not deploy session'
        deploy_sess = self.verify(10, self.deploy_session,
                                  4, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = 'Deploy did not complete correctly'
        status_env = self.verify(1800, self.deploy_check,
                                    5, fail_msg, 'deploy is going',
                                    self.environment.id)

        step = '6. Checking deployments status'
        deployment_status = self.verify(40, self.deployments_status_check,
                                        step, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = 'Cannot delete environment.'
        self.verify(5, self.delete_environment,
                    7, fail_msg, "deleting environment",
                    self.environment.id)

    def test_deploy_sql(self):
        """Check Murano API Service: Deploy SQL
        Test checks that user can deploy SQL.
        Target component: Murano

        Scenario:
            1. Send request to create environment.
            2. Send request to create session for environment.
            3. Send request to create service SQL.
            4. Request to deploy session.
            5. Checking environment status.
            6. Checking deployments status
            7. Send request to delete environment.
        Duration: 120 - 1830 s.
        """

        fail_msg = 'Cannot create environment.'
        self.environment = self.verify(5, self.create_environment,
                                       1, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = 'User can not create session for environment.'
        session = self.verify(5, self.create_session,
                              2, fail_msg, "session creating",
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
                              3, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = 'User can not deploy session'
        deploy_sess = self.verify(10, self.deploy_session,
                                  4, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = 'Deploy did not complete correctly'
        status_env = self.verify(1800, self.deploy_check,
                                    5, fail_msg, 'deploy is going',
                                    self.environment.id)

        step = '6. Checking deployments status'
        deployment_status = self.verify(40, self.deployments_status_check,
                                        step, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = 'Cannot delete environment.'
        self.verify(5, self.delete_environment,
                    7, fail_msg, "deleting environment",
                    self.environment.id)

    def test_deploy_sql_cluster(self):
        """Check Murano API Service: Deploy SQL
        Test checks that user can deploy SQL.
        Target component: Murano

        Scenario:
            1. Send request to create environment.
            2. Send request to create session for environment.
            3. Send request to create service AD.
            4. Request to deploy session.
            5. Checking environment status.
            6. Checking deployments status.
            7. Send request to create session for environment.
            8. Send request to create service SQL cluster.
            9. Request to deploy session..
            10. Checking environment status.
            11. Checking deployments status.
            12. Send request to delete environment.
        Duration: 200 - 2200 s.
        """

        fail_msg = 'Cannot create environment.'
        self.environment = self.verify(5, self.create_environment,
                                       1, fail_msg, 'creating environment',
                                       "ost1_test-Murano_env01")

        fail_msg = 'User can not create session for environment.'
        session = self.verify(5, self.create_session,
                              2, fail_msg, "session creating",
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
                              3, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = 'User can not deploy session'
        deploy_sess = self.verify(10, self.deploy_session,
                                  4, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = 'Deploy did not complete correctly'
        status_env = self.verify(1800, self.deploy_check,
                                    5, fail_msg, 'deploy is going',
                                    self.environment.id)

        deployment_status = self.verify(40, self.deployments_status_check,
                                        6, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = 'User can not create session for environment.'
        session = self.verify(5, self.create_session,
                              7, fail_msg, "session creating",
                              self.environment.id)

        # it is just 'any unused IP addresses'
        AG = self.config.murano.agListnerIP or '10.100.0.155'
        clIP = self.config.murano.clusterIP or '10.100.0.150'

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
                     "databases": []}

        fail_msg = 'User can not create service.'
        service = self.verify(5, self.create_service,
                              8, fail_msg, "service creating",
                              self.environment.id, session.id, post_body)

        fail_msg = 'User can not deploy session'
        deploy_sess = self.verify(10, self.deploy_session,
                                  9, fail_msg, "session send on deploy",
                                  self.environment.id, session.id)

        fail_msg = 'Deploy did not complete correctly'
        status_env = self.verify(1800, self.deploy_check,
                                    10, fail_msg, 'deploy is going',
                                    self.environment.id)

        step = '11. Checking deployments status'
        deployment_status = self.verify(40, self.deployments_status_check,
                                        step, fail_msg,
                                        'Check deployments status',
                                        self.environment.id)

        fail_msg = 'Cannot delete environment.'
        self.verify(5, self.delete_environment,
                    12, fail_msg, "deleting environment",
                    self.environment.id)
