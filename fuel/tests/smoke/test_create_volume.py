
from fuel.common.utils.data_utils import rand_name
from fuel.test import attr
from fuel.tests.smoke import base


class VolumesGetTestJSON(base.BaseComputeAdminTest):
    """
    Test class contains volume actions checks.
    """

    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(VolumesGetTestJSON, cls).setUpClass()
        cls.server = cls.create_server(wait_until='ACTIVE')[1]
        cls.client = cls.volumes_client
        cls.snapshot_client = cls.snapshots_client

    @attr(type=['fuel', 'smoke'])
    def test_volume_create_attach_delete(self):
        """
        Test contains the following steps:
          - create volume;
          - attach it to a new instance;
          - delete volume;
        """
        volume = None

        v_name = rand_name('Volume-%s-') % self._interface
        metadata = {'Type': 'work'}
        #Create volume
        resp, volume = self.client.create_volume(size=1,
                                                 display_name=v_name,
                                                 metadata=metadata)
        self.assertEqual(200, resp.status)
        self.assertTrue('id' in volume)

        # Wait for Volume status to become ACTIVE
        self.client.wait_for_volume_status(volume['id'], 'available')
        #GET Volume
        resp, fetched_volume = self.client.get_volume(volume['id'])
        self.assertEqual(200, resp.status)

        resp, body = self.client.attach_volume(volume, self.server)
        self.assertEqual(200, resp.status)

        if volume:
            #Delete the Volume created in this method
            resp, _ = self.client.delete_volume(volume['id'])
            self.assertEqual(202, resp.status)
            #Checking if the deleted Volume still exists
            self.client.wait_for_resource_deletion(volume['id'])



