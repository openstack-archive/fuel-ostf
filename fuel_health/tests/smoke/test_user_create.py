import requests
from nose.plugins.attrib import attr
from nose.tools import timed

from fuel_health.common.utils import data_utils
from fuel_health.tests.smoke import base


class TestUserTenantRole(base.BaseIdentityAdminTest):
    """
    Test class verifies the following:
      - verify tenant can be created;
      - verify user can be created on base of created tenant;
      - verify user role can be created.
    """

    _interface = 'json'

    alt_user = data_utils.rand_name('ost1_test-')
    alt_password = data_utils.rand_name('pass_')
    alt_email = alt_user + '@testmail.tm'
    alt_tenant = data_utils.rand_name('ost1_test-tenat')
    alt_description = data_utils.rand_name('ost1_test-desc_')
    alt_role = data_utils.rand_name('ost1_test-role_')

    @attr(type=["fuel", "smoke"])
    @timed(30.9)
    def test_create_user(self):
        """User creation and authentication.
        Target components: Nova, Keystone

        Scenario:
            1. Create a new tenant.
            2. Check tenant was created successfully.
            3. Create a new user.
            4. Check user was created successfully.
            5. Create a new user role.
            6. Check user role was created successfully.
            7. Perform token authentication.
            8. Check token authentication was successful.
            9. Check auth request to Horizon was successful.
            10. Check authentication to Horizon succeeded.
        Duration: 1-35 s.
        """
        # Create a tenant:
        try:
            resp, tenant = self.client.create_tenant(self.alt_tenant)
        except Exception as e:
            base.LOG.error("Tenant creation failed: %s" % e)
            self.fail('Step 1 failed: Create new tenant. Please, '
                      'check Keystone configuration ')
        self.verify_response_status(
                int(resp['status']), msg="Verify request was successful.",
                failed_step=2)

        # Create a user:
        try:
            resp, user = self.client.create_user(
                self.alt_user, self.alt_password, tenant['id'], self.alt_email)
        except Exception as e:
            base.LOG.error("User creation failed: %s" % e)
            self.fail("Step 3 failed: Create a new user. "
                      "Please, check Keystone service")
        self.verify_response_status(
            int(resp['status']), msg="Check user was created successfully.",
            failed_step=4)
        self.verify_response_body_value(user['name'], self.alt_user,
                                        failed_step=5)

        # Create a user role:
        try:
            resp, role = self.client.create_role(user['name'])
        except Exception as e:
            base.LOG.error("User role creation failed: %s" % e)
            self.fail("Step 6 failed: Create a new user role.")
        self.verify_response_status(
                int(resp['status']), msg="Check user role was created"
                                         " successfully.",
                                        failed_step=7)

        # Authenticate with created user:
        try:
            resp, body = self.token_client.auth(
                user['name'], self.alt_password, tenant['name'])
            self.verify_response_status(
                int(resp['status']), msg="Verify request was successful.",
                failed_step=8)

            # Auth in horizon with non-admin user
            client = requests.session()
            url = self.config.identity.url

            # Retrieve the CSRF token first
            client.get(url)  # sets cookie
            if len(client.cookies) == 0:
                login_data = dict(username=user['name'],
                                  password=self.alt_password,
                                  next='/')
                resp = client.post(url, data=login_data, headers=dict(Referer=url))
                self.verify_response_status(
                    resp.status_code, msg="Verify request was successful.",
                    failed_step=9)
            else:
                csrftoken = client.cookies['csrftoken']
                login_data = dict(username=user['name'],
                                  password=self.alt_password,
                                  csrfmiddlewaretoken=csrftoken,
                                  next='/')
                resp = client.post(url, data=login_data, headers=dict(Referer=url))
                self.verify_response_status(
                    resp.status_code, msg="Verify request was successful.",
                    failed_step=9)
        except Exception as e:
            self.LOG.error("Authentication to Horizon failed: %s" % e)
            self.fail("Step 10: Authenticate to Horizon failed, "
                      "please check Horizon is alive")
