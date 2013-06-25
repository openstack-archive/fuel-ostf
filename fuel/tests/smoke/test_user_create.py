import requests

from fuel.common.utils import data_utils
from fuel.test import attr
from fuel.tests.smoke import base


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
    def test_create_user(self):
        # Create a tenant:
        resp, tenant = self.client.create_tenant(self.alt_tenant)
        self.assertEqual('200', resp['status'])

        # Create a user:
        resp, user = self.client.create_user(self.alt_user, self.alt_password,
                                             tenant['id'],
                                             self.alt_email)
        self.assertEqual('200', resp['status'])
        self.assertEqual(self.alt_user, user['name'])

        # Create a user role:
        resp, role = self.client.create_role(user['name'])
        self.assertEqual('200', resp['status'])

        # Authenticate with created user:
        resp, body = self.token_client.auth(
            user['name'], self.alt_password, tenant['name'])
        self.assertEqual('200', resp['status'])

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
            self.assertEqual(resp.status_code, 200)

        else:
            csrftoken = client.cookies['csrftoken']
            login_data = dict(username=user['name'],
                          password=self.alt_password,
                          csrfmiddlewaretoken=csrftoken,
                          next='/')
            resp = client.post(url, data=login_data, headers=dict(Referer=url))
            self.assertEqual(resp.status_code, 200)
