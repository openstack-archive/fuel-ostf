from fuel.tests.sanity import base
from fuel.test import attr


class ServicesTestJSON(base.BaseIdentityAdminTest):
    _interface = 'json'

    @attr(type=['sanity', 'fuel'])
    def test_list_services(self):
        # List and Verify Services
        resp, body = self.client.list_services()
        self.assertEqual(200, resp.status)
        self.assertTrue(u'OS-KSADM:services' in body)

    @attr(type=['sanity', 'fuel'])
    def test_list_users(self):
        # List users
        resp, body = self.client.get_users()
        self.assertEqual(200, resp.status)
        self.assertTrue(u'users' in body)