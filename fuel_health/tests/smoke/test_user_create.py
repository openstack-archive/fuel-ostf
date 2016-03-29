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

import logging
import requests

from fuel_health import nmanager

LOG = logging.getLogger(__name__)


class TestUserTenantRole(nmanager.SmokeChecksTest):
    """Test class verifies the following:
      - verify that a tenant can be created;
      - verify that a user can be created based on the new tenant;
      - verify that a user role can be created.
    """

    def test_create_user(self):
        """Create user and authenticate with it.
        Target components: Nova, Keystone

        Scenario:
            1. Create a new tenant.
            2. Check that tenant was created successfully.
            3. Create a new user.
            4. Check that user was created successfully.
            5. Create a new user role.
            6. Check that user role was created successfully.
            7. Perform token authentication.
            8. Check that authentication was successful.
            9. Send authentication request to Horizon.
            10. Confirm that response status is 200.
        Duration: 80 s.
        """
        # Create a tenant:
        msg_s1 = 'Tenant can not be created. '

        tenant = self.verify(20, self._create_tenant, 1,
                             msg_s1, 'tenant creation', self.identity_client)

        self.verify_response_true(
            tenant.name.startswith('ost1_test'),
            "Step 2 failed: {msg}".format(msg=msg_s1))

        # Create a user:
        msg_s3 = "User can not be created."

        user = self.verify(20, self._create_user, 3, msg_s3,
                           'user creation', self.identity_client,
                           tenant.id)

        self.verify_response_true(
            user.name.startswith('ost1_test'),
            'Step 4 failed: {msg}'.format(msg=msg_s3))

        msg_s5 = "User role can not be created. "

        role = self.verify(20, self._create_role,
                           5, msg_s5,
                           'user role creation',
                           self.identity_client)

        self.verify_response_true(
            role.name.startswith('ost1_test'),
            "Step 6 failed: {msg}".format(msg=msg_s5))

        # Authenticate with created user:
        password = '123456'
        msg_s7 = "Can not get authentication token."

        auth = self.verify(40, self.identity_client.tokens.authenticate,
                           7, msg_s7,
                           'authentication',
                           username=user.name,
                           password=password,
                           tenant_id=tenant.id,
                           tenant_name=tenant.name)

        self.verify_response_true(auth,
                                  'Step 8 failed: {msg}'.format(msg=msg_s7))
        try:
            # Auth in horizon with non-admin user
            client = requests.session()
            if self.config.compute.deployment_os == 'Ubuntu':
                url = self.config.horizon_ubuntu_url
            else:
                url = self.config.horizon_url

            # Retrieve the CSRF token first
            client.get(url, verify=False)  # sets cookie
            if not len(client.cookies):
                login_data = dict(username=user.name,
                                  password=password,
                                  next='/')
                resp = client.post(url, data=login_data,
                                   headers=dict(Referer=url), verify=False)
                self.verify_response_status(
                    resp.status_code,
                    msg="Check that the request was successful. "
                        "Please refer to OpenStack logs for more details.",
                    failed_step=9)
            else:
                login_data = dict(username=user.name,
                                  password=password,
                                  next='/')
                csrftoken = client.cookies.get('csrftoken', None)
                if csrftoken:
                        login_data['csrfmiddlewaretoken'] = csrftoken

                resp = client.post(url, data=login_data,
                                   headers=dict(Referer=url), verify=False)
                self.verify_response_status(
                    resp.status_code,
                    msg="Check that the request was successful. "
                        "Please, refer to OpenStack "
                        "logs for more details.",
                    failed_step=9)
        except Exception as exc:
            LOG.exception(exc)
            self.fail("Step 10 failed: Can not authenticate in Horizon. "
                      "Please refer to OpenStack logs for more details.")
