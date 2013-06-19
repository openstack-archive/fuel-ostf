
from fuel.common.utils import data_utils
from fuel.test import attr
from fuel.tests.smoke import base


""" Test module contains tests for flavor creation/deletion. """

class FlavorsAdminTest(base.BaseComputeAdminTest):

    """
    Tests for flavor creation that require admin privileges.
    """

    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(FlavorsAdminTest, cls).setUpClass()

        cls.client = cls.os_adm.flavors_client
        cls.user_client = cls.os.flavors_client
        cls.flavor_name_prefix = 'test_flavor_'
        cls.ram = 256
        cls.vcpus = 1
        cls.disk = 0
        cls.ephemeral = 0
        cls.swap = 256
        cls.rxtx = 2

    @attr(type=["fuel", "smoke"])
    def test_create_flavor(self):
        """
        Test low requirements flavor creation.
        """
        # Create a flavor.
        # This operation requires the user to have 'admin' role.
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)

        #Create the flavor
        resp, flavor = self.client.create_flavor(flavor_name,
                                                 self.ram, self.vcpus,
                                                 self.disk,
                                                 new_flavor_id,
                                                 ephemeral=self.ephemeral,
                                                 swap=self.swap,
                                                 rxtx=self.rxtx)

        self.assertEqual(200, resp.status)
        self.assertEqual(flavor['name'], flavor_name)
        self.assertEqual(flavor['vcpus'], self.vcpus)
        self.assertEqual(flavor['disk'], self.disk)
        self.assertEqual(flavor['ram'], self.ram)
        self.assertEqual(int(flavor['id']), new_flavor_id)
        self.assertEqual(flavor['swap'], self.swap)
        self.assertEqual(flavor['rxtx_factor'], self.rxtx)
        self.assertEqual(flavor['OS-FLV-EXT-DATA:ephemeral'],
                         self.ephemeral)
       
        #Verify flavor is retrieved
        resp, flavor = self.client.get_flavor_details(new_flavor_id)
        self.assertEqual(resp.status, 200)

    # TODO: add teardown for this test.

