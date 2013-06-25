from fuel.test import attr
from fuel.tests.sanity import base


class NetworksTest(base.BaseNetworkTest):
    @attr(type=['sanity', 'fuel'])
    def test_list_networks(self):
        resp, body = self.client.list_networks()
        self.assertEqual(200, resp.status)
        self.assertTrue(u'networks' in body)

    @attr(type=['sanity', 'fuel'])
    def test_list_ports(self):
        resp, body = self.client.list_ports()
        self.assertEqual(200, resp.status)
        self.assertTrue(u'ports' in body)
