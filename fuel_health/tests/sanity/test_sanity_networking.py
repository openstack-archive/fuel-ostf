from nose.plugins.attrib import attr
from nose.tools import timed

from fuel_health.tests.sanity import base


class NetworksTest(base.BaseNetworkTest):
    """
    TestClass contains tests check base networking functionality
    """

    @attr(type=['sanity', 'fuel'])
    @timed(5.5)
    def test_list_networks(self):
        """Networks availability

        Test checks that available networks can be listed.
        Target component: Nova Networking.

        Scenario:
            1. Request list of networks.
            2. Check response status is equal to 200.
            3. Check response contains "networks" section.
        Duration: 0.3-5.6 s.
        """
        fail_msg = 'Network list is unavailable. ' \
                   'Looks like something is broken in Network ' \
                   '(Neutron or Nova).'
        try:
            resp, body = self.client.list_networks()
        except Exception as exc:
            base.error(exc)
            self.fail("Step 1 failed: " + fail_msg)
        self.verify_response_status(resp.status, u'Network (Neutron or Nova)',
                                    fail_msg, 2)
        self.verify_response_body(body, u'networks', fail_msg, 3)

    @attr(type=['sanity', 'fuel'])
    @timed(5.5)
    def test_list_ports(self):
        """Ports availability

        Test checks that existing ports can be listed.
        Target component: Nova Networking.

        Scenario:
            1. Request list of ports.
            2. Check response status is equal to 200.
            3. Check response contains "ports" section.
        Duration: 0.2-5.6 s.
        """
        fail_msg = 'Ports list is unavailable. ' \
                   'Looks like something is broken in Network ' \
                   '(Neutron or Nova).'
        try:
            resp, body = self.client.list_ports()
        except Exception as exc:
            base.error(exc)
        self.verify_response_status(resp.status, u'Network (Neutron or Nova)',
                                    fail_msg, 2)
        self.verify_response_body(body, u'ports', fail_msg, 3)