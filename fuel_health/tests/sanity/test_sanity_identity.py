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
        """ Test checks that active services can be listed.
        Target component: Nova

        Scenario:
            1. Request list of services.
            2. Check response status is equal to 200.
            3. Check response contains "OS-KSADM:services" section.
        Duration: 0.2-5.6 s.
        """
        fail_msg = u'Services list is unavailable. ' \
                   u'Looks like something is broken in Nova.'
        try:
            resp, body = self.client.list_services()
        except Exception as exc:
            self.error(exc._error_string)
            self.fail("Step 1 failed: " + fail_msg)
        self.verify_response_status(resp.status, u'Nova', fail_msg, 2)
        self.verify_response_body(body, u'OS-KSADM:services',fail_msg, 3)

    @attr(type=['sanity', 'fuel'])
    @timed(5.5)
    def test_list_users(self):
        """Test checks that existing users can be listed.
        Target component: Keystone

        Scenario:
            1. Request list of users.
            2. Check response status is equal to 200.
            3. Check response contains "users" section.
        Duration: 0.2-5.6 s.
        """
        fail_msg = u'Users list is unavailable. ' \
                   u'ooks like something is broken in Keystone.'
        try:
            resp, body = self.client.get_users()
        except Exception as exc:
            self.error(exc._error_string)
            self.fail("Step 1 failed: " + fail_msg)
        self.verify_response_status(resp.status, u'Keystone', fail_msg, 2)
        self.verify_response_body(body, u'users',fail_msg, 3)
