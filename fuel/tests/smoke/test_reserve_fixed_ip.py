
from fuel.test import attr
from fuel.tests.smoke import base

class FixedIPsTestJson(base.FixedIPsBase):
    """
    Test class contains the following verifications:
      - fixed ip reservation test;
      - fixed ip unreservation test.
    """
    _interface = 'json'

    @attr(type=['fuel', 'smoke'])
    def test_set_reserve(self):
        body = {"reserve": "None"}
        resp, body = self.client.reserve_fixed_ip(self.ip, body)
        self.assertEqual(resp.status, 202)

    @attr(type=['fuel', 'smoke'])
    def test_set_unreserve(self):
        body = {"unreserve": "None"}
        resp, body = self.client.reserve_fixed_ip(self.ip, body)
        self.assertEqual(resp.status, 202)


