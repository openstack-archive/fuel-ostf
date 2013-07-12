from fuel_health.tests.sanity import base
from fuel_health.test import attr


class ServicesTestJSON(base.BaseIdentityAdminTest):
    """
    TestClass contains tests check base authentication functionality.
    Special requirements: OS admin user permissions needed
    """
    _interface = 'json'

    @attr(type=['sanity', 'fuel'])
    def test_list_services(self):
        """Test checks that active services can be listed."""
        resp, body = self.client.list_services()
        self.verify_response_status(resp.status, u'Nova')
        self.verify_response_body(body, u'OS-KSADM:services',
                                  u'Services list is unavailable. '
                                  u'Looks like something`s broken in Nova.')

    @attr(type=['sanity', 'fuel'])
    def test_list_users(self):
        """Test checks that existing users can be listed."""
        resp, body = self.client.get_users()
        self.verify_response_status(resp.status, u'Keystone')
        self.verify_response_body(body, u'users',
                                  u'Users list is unavailable. '
                                  u'Looks like something`s broken in Keystone.')
