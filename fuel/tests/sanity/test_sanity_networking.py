
from fuel.sanity import base
from fuel.test import attr


class NetworksTest(base.BaseNetworkTest):
    @attr(type='sanity')
    def test_list_networks(self):
        resp, body = self.client.list_networks()
        self.assertEqual(200, resp.status)
        self.assertTrue(u'networks' in body)


    @attr(type='sanity')
    def test_list_ports(self):
        resp, body = self.client.list_ports()
        self.assertEqual(200, resp.status)
        self.assertTrue(u'ports' in body)