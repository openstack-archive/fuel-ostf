
from fuel.common.utils import data_utils
from fuel.test import attr
from fuel.tests.smoke import base

class SecurityGroupsTest(base.BaseComputeTest):
    """
    Test security group creation.
    """
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(SecurityGroupsTest, cls).setUpClass()
        cls.client = cls.security_groups_client

    def _delete_security_group(self, securitygroup_id):
        resp, _ = self.client.delete_security_group(securitygroup_id)
        self.assertEqual(202, resp.status)

    @attr(type=['fuel', 'smoke'])
    def test_security_group_create_delete(self):
        # Security Group should be created, verified and deleted
        s_name = data_utils.rand_name('securitygroup-')
        s_description = data_utils.rand_name('description-')

        resp, securitygroup = \
            self.client.create_security_group(s_name, s_description)
        self.assertTrue('id' in securitygroup)
        securitygroup_id = securitygroup['id']

        self.addCleanup(self._delete_security_group,
                        securitygroup_id)
        self.assertEqual(200, resp.status)
        self.assertFalse(securitygroup_id is None)
        self.assertTrue('name' in securitygroup)
        securitygroup_name = securitygroup['name']
        self.assertEqual(securitygroup_name, s_name,
                         "The created Security Group name is not equal to the requested name")

