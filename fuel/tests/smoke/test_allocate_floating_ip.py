
from fuel.common.utils.data_utils import rand_name
from fuel.test import attr
from fuel.tests.smoke import base

class FloatingIPsTestJSON(base.BaseComputeAdminTest):
    _interface = 'json'
    server_id = None
    floating_ip = None

    @classmethod
    def setUpClass(cls):
        super(FloatingIPsTestJSON, cls).setUpClass()
        cls.client = cls.floating_ips_client
        cls.servers_client = cls.servers_client

        #Server creation
        resp, server = cls.create_server(wait_until='ACTIVE')
        cls.server_id = server['id']
        resp, body = cls.servers_client.get_server(server['id'])

        #Floating IP creation
        resp, body = cls.client.create_floating_ip()
        cls.floating_ip_id = body['id']
        cls.floating_ip = body['ip']
        #Generating a nonexistent floatingIP id
        cls.floating_ip_ids = []
        resp, body = cls.client.list_floating_ips()
        for i in range(len(body)):
            cls.floating_ip_ids.append(body[i]['id'])
        while True:
            cls.non_exist_id = rand_name('999')
            if cls.non_exist_id not in cls.floating_ip_ids:
                break


    @attr(type=['fuel', 'smoke'])
    def test_allocate_floating_ip(self):
        # Positive test:Allocation of a new floating IP to a project
        # should be successful
        resp, ip_body = self.client.create_floating_ip()
        self.assertEqual(200, resp.status)
        floating_ip_id_allocated = ip_body['id']
        resp, floating_ip_details = \
            self.client.get_floating_ip_details(floating_ip_id_allocated)
        #Checking if the details of allocated IP is in list of floating IP
        resp, body = self.client.list_floating_ips()
        self.assertTrue(floating_ip_details in body)

        resp, body = self.client.associate_floating_ip_to_server(floating_ip_details['ip'], self.server_id)
        self.assertTrue(200, resp.status)
        resp, body = self.client.disassociate_floating_ip_from_server(floating_ip_details['ip'], self.server_id)
        self.assertTrue(200, resp.status)

        #Deleting the floating IP which is created in this method
        self.client.delete_floating_ip(floating_ip_id_allocated)
        self.assertTrue(200, resp.status)


