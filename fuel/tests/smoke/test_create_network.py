import netaddr

from fuel.common.utils import data_utils
from fuel.test import attr
from fuel.tests.smoke import base


"""
Test module for network creation.

Dependencies:
v2.0 of the Quantum API is assumed. It is also assumed that the following
options are defined in the [network] section of etc/tempest.conf:

  - tenant_network_cidr with a block of cidr's from which smaller blocks
    can be allocated for tenant networks;
  - tenant_network_mask_bits with the mask bits to be used to partition the
    block defined by tenant-network_cidr.
"""

class NetworksTest(base.BaseComputeTest):

    """
    Test class for tenant netwprk creation the Quantum API using the REST client for
    Quantum.
    """
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(NetworksTest, cls).setUpClass()


    @attr(type=["fuel", "smoke"])
    def test_create_network(self):
        """ Test network creation. """
        network_name = data_utils.rand_name('test-network-')

        resp, body = self.network_client.create_network(network_name)
        network = body['network']
        self.assertEqual(body['name'], network_name)
        self.assertTrue(network['id'] is not None)

        cidr = netaddr.IPNetwork(self.network_cfg.tenant_network_cidr)

    #TODO: finish this test (it`s incomplete for now).
    #TODO: add teardown for this test.


