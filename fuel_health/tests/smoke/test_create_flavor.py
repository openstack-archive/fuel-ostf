
from fuel_health.test import attr
from fuel_health.tests.smoke import base


""" Test module contains tests for flavor creation/deletion. """


class FlavorsAdminTest(base.BaseComputeAdminTest):

    """
    Tests for flavor creation that require admin privileges.
    """

    _interface = 'json'

    @attr(type=["fuel", "smoke"])
    def test_create_flavor(self):
        """
        Test low requirements flavor creation.
        """
        resp, flavor = self.create_flavor(ram=255,
                                          name='ost1_test-flavor-smoke-test',
                                          disk=1)

        self.verify_response_status(resp.status)
        self.verify_response_body_value(
            flavor['name'], u'ost1_test-flavor-smoke-test')
        self.verify_response_body_value(flavor['disk'], 1)
        self.verify_response_body(flavor, 'id')
