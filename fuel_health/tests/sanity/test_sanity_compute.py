from fuel_health.test import attr
from fuel_health.tests.sanity import base


class SanityComputeTest(base.BaseComputeTest):
    """
    TestClass contains tests check base Compute functionality.
    """
    _interface = 'json'

    @attr(type=['sanity', 'fuel'])
    def test_list_instances(self):
        """
        Test checks that existing instances can be listed.
        """
        resp, body = self.servers_client.list_servers()
        self.verify_response_status(resp.status, u'Nova')
        self.verify_response_body(body, u'servers',
                                  'Servers list is unavailable. '
                                  'Looks like something broken in Nova.')

    @attr(type=['sanity', 'fuel'])
    def test_list_images(self):
        """
        Test checks that existing images can be listed.
        """
        resp, body = self.images_client.list_images()
        self.verify_response_status(resp.status, 'Glance')
        self.verify_response_body(body, u'images',
                                  'Images list is unavailable. '
                                  'Looks like something broken in Glance.')

    @attr(type=['sanity', 'fuel'])
    def test_list_volumes(self):
        """
        Test checks that existing volumes can be listed.
        """
        resp, body = self.volumes_client.list_volumes()
        self.verify_response_status(resp.status, 'Swift')
        self.verify_response_body(body, u'volumes',
                                  'Volumes list is unavailable. '
                                  'Looks like something broken in Swift.')

    @attr(type=['sanity', 'fuel'])
    def test_list_snapshots(self):
        """
        Test checks that existing snapshots can be listed.
        """
        resp, body = self.snapshots_client.list_snapshots()
        self.verify_response_status(resp.status, 'Swift')
        self.verify_response_body(body, u'snapshots',
                                  'Snapshots list is unavailable. '
                                  'Looks like something broken in Swift.')

    @attr(type=['sanity', 'fuel'])
    def test_list_flavors(self):
        """
        Test checks that existing flavors can be listed.
        """
        resp, body = self.flavors_client.list_flavors()
        self.verify_response_status(resp.status, 'Nova')
        self.verify_response_body(body, u'flavors',
                                  'Flavors list is unavailable. '
                                  'Looks like something broken in Nova.')

    @attr(type=['sanity', 'fuel'])
    def test_list_rate_limits(self):
        """
        Test checks that absolute limits can be listed.
        """
        resp, body = self.limits_client.get_absolute_limits()
        self.verify_response_status(resp.status, 'Nova')
        self.verify_response_body(body["limits"], u'absolute',
                                  'Limits are unavailable. '
                                  'Looks like something broken in Nova.')
