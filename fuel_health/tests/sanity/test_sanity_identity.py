from nose.plugins.attrib import attr
from nose.tools import timed

from fuel_health.tests.sanity import base


class ServicesTestJSON(base.BaseIdentityAdminTest):
    """
    TestClass contains tests check base authentication functionality.
    Special requirements: OS admin user permissions needed
    """
    _interface = 'json'

    @attr(type=['sanity', 'fuel'])
    @timed(5.5)
    def test_list_services(self):
        """Test checks that active services can be listed."""
        resp, body = self.client.list_services()
        self.verify_response_status(resp.status, u'Nova')
        self.verify_response_body(body, u'OS-KSADM:services',
                                  u'Services list is unavailable. '
                                  u'Looks like something is broken in Nova.')

    @attr(type=['sanity', 'fuel'])
    @timed(5.5)
    def test_list_users(self):
        """Test checks that existing users can be listed."""
        resp, body = self.client.get_users()
        self.verify_response_status(resp.status, u'Keystone')
        self.verify_response_body(body, u'users',
                                  u'Users list is unavailable. '
                                  u'Looks like something is broken in Keystone.')
