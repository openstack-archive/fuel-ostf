
from fuel.sanity import base
from fuel.test import attr


class SanityComputeTest(base.BaseComputeTest):
    _interface = 'json'

    @attr(type='sanity')
    def test_list_instances(self):
        resp, body = self.servers_client.list_servers()
        self.assertEqual(200, resp.status)
        self.assertTrue(u'servers' in body)

    @attr(type='sanity')
    def test_list_images(self):
        resp, body = self.images_client.list_images()
        self.assertEqual(200, resp.status)
        self.assertTrue(u'images' in body)

    @attr(type='sanity')
    def test_list_volumes(self):
        resp, body = self.volumes_client.list_volumes()
        self.assertEqual(200, resp.status)
        self.assertTrue(u'volumes' in body)

    @attr(type='sanity')
    def test_list_snapshots(self):
        resp, body = self.snapshots_client.list_snapshots()
        self.assertEqual(200, resp.status)
        self.assertTrue(u'snapshots' in body)

    @attr(type='sanity')
    def test_list_flavors(self):
        resp, body = self.flavors_client.list_flavors()
        self.assertEqual(200, resp.status)
        self.assertTrue(u'flavors' in body)

    @attr(type='sanity')
    def test_list_rate_limits(self):
        resp, body = self.limits_client.get_absolute_limits()
        self.assertEqual(200, resp.status)
        self.assertTrue(u'absolute' in body["limits"])