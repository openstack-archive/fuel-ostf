from fuel.test import attr
from fuel.tests.smoke import base


class SecurityGroupsTest(base.BaseComputeTest):
    """
    Test security group creation.
    """
    _interface = 'json'

    @attr(type=['fuel', 'smoke'])
    def test_security_group_create(self):
        """
        Verify security group can be created by admin user.
        """

        resp, securitygroup = self.create_sec_group(
            name='ost1_test-sec_group-smoke-test',
            description='ost1_test-description-smoke-descr')

        self.verify_response_status(resp.status)
        self.verify_response_body(securitygroup, 'id')

        self.verify_response_body_value(
            securitygroup['name'],
            u'ost1_test-sec_group-smoke-test')
        self.verify_response_body_value(
            securitygroup['description'],
            u'ost1_test-description-smoke-descr')
