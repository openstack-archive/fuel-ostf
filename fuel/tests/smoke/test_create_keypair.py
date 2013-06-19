
from fuel.common.utils import data_utils
from fuel.test import attr
from fuel.tests.smoke import base


class KeyPairsTestJSON(base.BaseComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(KeyPairsTestJSON, cls).setUpClass()
        cls.client = cls.keypairs_client

    @attr(type=['fuel', 'smoke'])
    def test_keypair_create_delete(self):
        """ Test keypair creation and deletion. """
        k_name = data_utils.rand_name('keypair-')
        resp, keypair = self.client.create_keypair(k_name)
        self.assertEqual(200, resp.status)
        private_key = keypair['private_key']
        key_name = keypair['name']
        self.assertEqual(key_name, k_name,
                         "The created keypair name is not equal "
                         "to the requested name")
        self.assertTrue(private_key is not None,
                        "Field private_key is empty or not found.")
        resp, _ = self.client.delete_keypair(k_name)
        self.assertEqual(202, resp.status)

    # TODO: add teardown for this test.

