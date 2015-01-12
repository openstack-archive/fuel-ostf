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

from fuel_health import muranomanager


class MuranoSanityTests(muranomanager.MuranoTest):
    """
    TestClass contains verifications of basic Murano functionality.
    Special requirements:
        1. Murano API service should be installed.
    """

    def test_create_and_delete_service(self):
        """Create and delete Murano environment
        Target component: Murano

        Scenario:
            1. Send request to create environment.
            2. Send request to delete environment.

        Duration: 10 s.

        Deployment tags: Murano
        """

        fail_msg = "Can't create environment. Murano API isn't available. "
        self.environment = self.verify(15, self.create_environment,
                                       1, fail_msg, "creating environment",
                                       "ost1_test-Murano_env01")

        fail_msg = ("Can't delete environment. Murano API isn't available "
                    "or RabbitMQ connectivity broken. ")
        self.verify(5, self.delete_environment, 2, fail_msg,
                    "deleting environment", self.environment['id'])

    def test_get_list_categories(self):
        """Get list of Murano applications categories
        Target component: Murano

        Scenario:
            1. Send request to get list of categories

        Duration: 10 s.

        Deployment tags: Murano
        """
        fail_msg = "Can't get list of categories. Murano API isn't available. "
        self.verify(10, self.get_list_categories, 1, fail_msg,
                    "getting list of categories")

    def test_get_list_packages(self):
        """Get list of Murano applications packages
        Target component: Murano

        Scenario:
            1. Send request to get list of packages

        Duration: 10 s.

        Deployment tags: Murano
        """
        fail_msg = "Can't get list of packages. Murano API isn't available. "
        self.verify(10, self.get_list_packages, 1, fail_msg,
                    "getting list of packages")
