import logging

import requests
from nose.plugins.attrib import attr
from nose.tools import timed

from fuel_health.common.utils import data_utils
from fuel_health import nmanager

LOG = logging.getLogger(__name__)


class TestUserTenantRole(nmanager.SmokeChecksTest):
    """
    Test class verifies the following:
      - verify tenant can be created;
      - verify user can be created on base of created tenant;
      - verify user role can be created.
    """

    _interface = 'json'

    @attr(type=["fuel", "smoke"])
    @timed(30.9)
    def test_create_user(self):
        """ Test verifies user creation and auth in Horizon
        Target components: Nova, Keystone

        Scenario:
            1. Create a new tenant.
            2. Check tenant was created successfully.
            3. Create a new user.
            4. Check user was created successfully.
            5. Create a new user role.
            6. Check user role was created successfully.
            7. Perform token authentication.
            8. Check authentication was successful.
            9. Send authentication request to Horizon.
            10. Verify response status is 200.
        Duration: 1-30.9 s.
        """
        # Create a tenant:
        msg_s1 = ('Tenant creation failure, please, '
                  'check Keystone configuration ')
        try:
            tenant = self._create_tenant(self.identity_client)

        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 1 failed: " + msg_s1)

        self.verify_response_true(
            tenant.name.startswith('ost1_test'),
            "Step 2 failed: " + msg_s1)


        # Create a user:
        msg_s3 = "Can't create a user. Please, check Keystone service"
        try:
            user = self._create_user(self.identity_client, tenant.id)

        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 3 failed: " + msg_s3)

        self.verify_response_true(
            user.name.startswith('ost1_test'),
            'Step 4 failed: ' + msg_s3)

        msg_s5 = "User role creation fails. Please, check Keystone service"

        try:
            role = self._create_role(self.identity_client)
        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 5 failed: " + msg_s5)

        self.verify_response_true(
            role.name.startswith('ost1_test'),
            "Step 6 failed: " + msg_s5)


        # # Authenticate with created user:
        password = '123456'
        msg_s7 = "Can not get auth token, check Keystone service"
        try:
            auth = self.identity_client.tokens.authenticate(
                username=user.name, password=password, tenant_id=tenant.id,
                tenant_name=tenant.name)
        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 7 failed: " + msg_s7)

        self.verify_response_true(auth, 'Step 8 failed: ' + msg_s7)

        try:
            #Auth in horizon with non-admin user
            client = requests.session()
            url = self.config.identity.url

            # Retrieve the CSRF token first
            client.get(url)  # sets cookie
            if not len(client.cookies):
                login_data = dict(username=user.name,
                                  password=password,
                                  next='/')
                resp = client.post(url, data=login_data, headers=dict(Referer=url))
                self.verify_response_status(
                    resp.status_code, msg="Verify request was successful.")
            else:
                csrftoken = client.cookies['csrftoken']
                login_data = dict(username=user.name,
                                  password=password,
                                  csrfmiddlewaretoken=csrftoken,
                                  next='/')
                resp = client.post(url, data=login_data, headers=dict(Referer=url))
                self.verify_response_status(
                    resp.status_code, msg="Verify request was successful.")
        except Exception:
            self.fail("Can not auth in Horizon, please check Horizon is alive")
