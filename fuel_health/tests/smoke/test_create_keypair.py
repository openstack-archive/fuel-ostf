from fuel.test import attr
from fuel.tests.smoke import base


class KeyPairsTestJSON(base.BaseComputeTest):
    _interface = 'json'

    @attr(type=['fuel', 'smoke'])
    def test_keypair_create_delete(self):
        """
        Verify keypair can be created by admin user.
        """
        resp, keypair = self.create_keypair(
            name='ost1_test-keypair-smoke-test')
        self.verify_response_status(resp.status)

        self.verify_response_body_value(
            keypair, u'ost1_test-keypair-smoke-test',
            "The created keypair name is not equal to the requested name")
        self.verify_response_body(
            keypair, 'private_key',
            "Field private_key is empty or not found.")
