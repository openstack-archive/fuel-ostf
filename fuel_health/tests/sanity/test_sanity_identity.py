import logging

from nose.plugins.attrib import attr
from nose.tools import timed

from fuel_health import nmanager

LOG = logging.getLogger(__name__)


class ServicesTestJSON(nmanager.SanityChecksTest):
    """
    TestClass contains tests check base authentication functionality.
    Special requirements: OS admin user permissions needed
    """
    _interface = 'json'

    @attr(type=['sanity', 'fuel'])
    @timed(6)
    def test_list_services(self):
        """Services list availability
        Test checks that active services can be listed.
        Target component: Nova

        Scenario:
            1. Request list of services.
            2. Check response.
        Duration: 1-6 s.
        """
        fail_msg = ('Services list is unavailable. '
                    'Looks like something is broken in Nova or Keystone.')
        try:
            services = self._list_services(self.compute_client)
        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 1 failed: " + fail_msg)
        self.verify_response_true(len(services) >= 0, "Step 2 failed: " + fail_msg)

    @attr(type=['sanity', 'fuel'])
    @timed(6)
    def test_list_users(self):
        """User list availability
        Test checks that existing users can be listed.
        Target component: Keystone

        Scenario:
            1. Request list of users.
            2. Check response.
        Duration: 1-6 s.
        """
        fail_msg = ('Users list is unavailable. '
                    'Looks like something is broken in Keystone.')
        try:
            users = self._list_users(self.identity_client)
        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 1 failed: " + fail_msg)
        self.verify_response_true(len(users) >= 0, "Step 2 failed: " + fail_msg)

