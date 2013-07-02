from fuel.test import attr
from fuel.tests.smoke import base


class NetworksTest(base.BaseComputeTest):

    """
    Test class for tenant network creation the Quantum API using the REST
    client for Quantum.
    """

    _interface = 'json'

    @attr(type=["fuel", "smoke"])
    def test_create_network(self):
        """ Test network creation. """

        resp, body = self.create_network(
            name='ost1_test-network-smoke-network')
        self.verify_response_status(resp.status)
        self.verify_response_body_value(body, u'ost1_test-network-smoke-network')
        self.verify_response_body(body, 'id')
