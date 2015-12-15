#copyright 2013 Mirantis, Inc.

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import heatclient.v1.client
import keystoneclient
from  fuel_health import heatmanager, nmanager, exceptions
import traceback


LOG = logging.getLogger(__name__)
class TestLdapUser(nmanager.SmokeChecksTest, nmanager.OfficialClientManager):

    def setUp(self):
        super(TestUser, self).setUp()
        if not self.config.compute.compute_nodes:
            self.skipTest('There are no compute nodes')

    def add_user_to_new_project(self):
        
        self.check_image_exists()

        # Create a new project in keystone domain using default user:
        msg_s1 = 'Tenant V3 can not be created. '
        # Create_tenants-nmanager
        
        clientV3 = self._get_identity_client(version=3,
                                             username='admin',
                                             password='admin',
                                             user_domain_name='default')

        tenant = self.verify(60, self._create_tenant, 1,
                             msg_s1, 'tenant creation', clientV3,
                             project_name='KeystoneV3',
                             domain_name='r1_ldap.com')

        self.verify_response_true(
            tenant.name.startswith('KeystoneV3'),
            "Step 2 failed: {msg}".format(msg=msg_s1))
        print "all OK"

        # Update user: add user to existing domain project. We cant verify this action
        msg_u1 = 'User V3 can not be updated. Verify LDAP server or Project preference '
        user_update = self.verify(60, self._update_user, 2,
                             msg_u1, 'user update', clientV3,
                             user_name ='Administrator',
                             tenant= tenant,
                             domain_name='r1_ldap.com')
        return tenant

class TestStack(heatmanager.HeatBaseTest, TestLdapUser):
        
        def test_autoscaling_ldap(self):
            """Advanced stack actions: Check stack using LDAP server
            Target component: Heat

            Scenario:
                1. Create tenant in LDAP domain
                2. Add user to tenant
                3. Create test flavor in LDAP domain.
                4. Create a keypair.
                5. Save generated private key to file on Controller node.
                6. Create a security group?.
                7. Create a stack in LDAP domain.
                8. Wait for the stack status to change to 'CREATE_COMPLETE'.
                9. Create a floating IP.
                10. Assign the floating IP to the instance of the stack.
                11. Wait for instance is ready for load.
                12. Load the instance CPU to initiate the stack scaling up.
                13. Wait for the 2nd instance to be launched.
                14. Release the instance CPU to initiate the stack scaling down.
                15. Wait for the 2nd instance to be terminated.
                16. Delete the file with private key.
                17. Delete the stack.
                18. Wait for the stack to be deleted.

            Duration: 1600 s.
            """
            # Iniciate same parameters. It's needed for stack creation in LDAP domain
            username = 'Administrator'
            password ='qwerty123'
            user_domain_name ='r1_ldap.com'
            tenant = TestLdapUser.add_user_to_new_project(self)
            tenant_name = tenant.name
            project_id = tenant.id

            comute_ldap_client = self._get_compute_client(username='Administrator',
                                                          password='qwerty123',
                                                          tenant_name=project_id)

            heat_ldap_client = self._get_heat_client(username=username,
                                                     password=password,
                                                     tenant_name=tenant_name,
                                                     version=3,
                                                     user_domain_name=user_domain_name,
                                                     project_id=project_id)
            self.check_image_exists()

            # creation of test flavor - NO!! edit create flavor
            heat_flavor = self.verify(
                50, self.create_flavor,
                3, 'Test flavor can not be created.',
                'flavor creation'                
            )

            # definition of stack parameters
            parameters = {
                'InstanceType': heat_flavor.name,
                'ImageId': self.config.compute.image_name,
            }

            # create net
            parameters['Subnet'], _ = self.create_network_resources(
                                                   project_id=project_id)
            template = self.load_template('heat_autoscaling_ldap_neutron.yaml')

            # creation of stack - add heat client and edit heatmenager
            fail_msg = 'Stack was not created properly.'
            stack = self.verify(
                600, self.create_stack,
                7, fail_msg,
                'stack creation',
                template, parameters=parameters,
                client = heat_ldap_client
            )
            self.verify(
                600, self.wait_for_stack_status,
                8, fail_msg,
                'stack status becoming "CREATE_COMPLETE"',
                stack.id, 'CREATE_COMPLETE', 600, 15
            )


            reduced_stack_name = '{0}-{1}'.format(
                stack.stack_name[:2], stack.stack_name[-4:])

            instances = self.get_instances_by_name_mask(reduced_stack_name, client=comute_ldap_client)
            self.verify(
                2, self.assertTrue,
                9, 'Instance for the stack was not created.',
                'verifying the number of instances after template update',
                len(instances) != 0
            )

            # assigning floating ip
            floating_ip = self.verify(
                10, self._create_floating_ip,
                10, 'Floating IP can not be created.',
                'floating IP creation',
                client=comute_ldap_client
            )
            self.verify(
                20, self._assign_floating_ip_to_instance,
                11, 'Floating IP can not be assigned.',
                'assigning floating IP',
                comute_ldap_client, instances[0], floating_ip
            )

            # vm connection check
            vm_connection = ('ssh -o StrictHostKeyChecking=no -i {0} {1}@{2}'.
                             format(path_to_key, 'cirros', floating_ip.ip))

            self.verify(
                120, self.wait_for_vm_ready_for_load,
                12, 'VM is not ready or connection can not be established.',
                'test script execution on VM',
                vm_connection, 120, 15
            )

            # start of vm loading
            self.verify(
                60, self.load_vm_cpu,
                13, 'Can not create a process to load VM CPU.',
                'loading VM CPU',
                vm_connection
            )

            # launching the second instance during autoscaling
            self.verify(
                480, self.wait_for_autoscaling,
                14, 'Failed to launch the 2nd instance per autoscaling alarm.',
                'launching the new instance per autoscaling alarm',
                len(instances) + 1, 480, 10, reduced_stack_name, client=comute_ldap_client
            )

            # finish of vm loading
            self.verify(
                180, self.release_vm_cpu,
                15, 'Can not kill the process on VM to turn CPU load off.',
                'turning off VM CPU load',
                vm_connection
            )

            # termination of the second instance during autoscaling
            self.verify(
                480, self.wait_for_autoscaling,
                16, 'Failed to terminate the 2nd instance per autoscaling alarm.',
                'terminating the 2nd instance per autoscaling alarm',
                len(instances), 480, 10, reduced_stack_name, client=comute_ldap_client
            )

            # deletion of stack
            self.verify(
                20, heat_ldap_client.stacks.delete,
                18, 'Can not delete stack.',
                'deleting stack',
                stack.id
            )
            self.verify(
                100, self.wait_for_stack_deleted,
                19, 'Can not delete stack.',
                'deleting stack',
                stack.id
            )
