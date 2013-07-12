from fuel_health.tests.sanity import base
from nose.plugins.attrib import attr


class ServicesTestJSON(base.BaseIdentityAdminTest):
    """
    TestClass contains tests check base authentication functionality.
    Special requirements: OS admin user permissions needed
    """
    _interface = 'json'

    @attr(type=['sanity', 'fuel'])
    def test_list_services(self):
        """
        Test checks list of active services is available.
        Target component: Nova
        Special requirements: OS admin user permissions needed

        Scenario:
            1. Request list of services.
            2. Check response status is equal to 200.
            3. Check response contains appropriate section.
        """
        resp, body = self.client.list_services()
        self.verify_response_status(resp.status, u'Nova')
        self.verify_response_body(body, u'OS-KSADM:services',
                                  u'Services list is unavailable. '
                                  u'Looks like something broken in Nova.')

    @attr(type=['sanity', 'fuel'])
    def test_list_users(self):
        """
        Test checks list of users available.
        Target component: Keystone
        Special requirements: OS admin user permissions needed

        Scenario:
            1. Request list of users.
            2. Check response status is equal to 200.
            3. Check response contains "users" section.
        """
        resp, body = self.client.get_users()
        self.verify_response_status(resp.status, u'Keystone')
        self.verify_response_body(body, u'users',
                                  u'Users list is unavailable. '
                                  u'Looks like something broken in Keystone.')
