# Copyright 2013 Mirantis, Inc.

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

from fuel_health import heatmanager


LOG = logging.getLogger(__name__)


class HeatSmokeTests(heatmanager.HeatBaseTest):
    """Test class verifies Heat API calls, rollback and
    autoscaling use-cases.
    """
    def setUp(self):
        super(HeatSmokeTests, self).setUp()
        if not self.config.compute.compute_nodes:
            self.skipTest('There are no compute nodes')

    def test_advanced_actions(self):
        """Advanced stack actions: suspend, resume and check
        Target component: Heat

        Scenario:
            1. Create test flavor.
            2. Create a stack.
            3. Wait until the stack status will change to 'CREATE_COMPLETE'.
            4. Call stack suspend action.
            5. Wait until the stack status will change to 'SUSPEND_COMPLETE'.
            6. Check that stack resources are in 'SUSPEND_COMPLETE' status.
            7. Check that server owned by stack is in 'SUSPENDED' status.
            8. Call stack resume action.
            9. Wait until the stack status will change to 'RESUME_COMPLETE'.
            10. Check that stack resources are in 'RESUME_COMPLETE' status.
            11. Check that instance owned by stack is in 'ACTIVE' status.
            12. Call stack check action.
            13. Wait until the stack status will change to 'CHECK_COMPLETE'.
            14. Check that stack resources are in 'CHECK_COMPLETE' status.
            15. Check that instance owned by stack is in 'ACTIVE' status.
            16. Delete the stack and wait for the stack to be deleted.

        Duration: 660 s.
        Available since release: 2014.2-6.1
        """

        self.check_image_exists()

        # create test flavor
        fail_msg = 'Test flavor was not created.'
        heat_flavor = self.verify(
            60, self.create_flavor,
            1, fail_msg,
            'flavor creation'
        )

        # define stack parameters
        parameters = {
            'InstanceType': heat_flavor.name,
            'ImageId': self.config.compute.image_name
        }
        if 'neutron' in self.config.network.network_provider:
            parameters['network'] = self.private_net
            template = self.load_template(
                'heat_create_neutron_stack_template.yaml')
        else:
            template = self.load_template(
                'heat_create_nova_stack_template.yaml')

        # create stack
        fail_msg = 'Stack was not created properly.'
        stack = self.verify(
            20, self.create_stack,
            2, fail_msg,
            'stack creation',
            template, parameters=parameters
        )
        self.verify(
            300, self.wait_for_stack_status,
            3, fail_msg,
            'stack status becoming "CREATE_COMPLETE"',
            stack.id, 'CREATE_COMPLETE'
        )
        res = self.get_stack_resources(
            stack.id,
            key='resource_type', value='OS::Nova::Server'
        )

        # suspend stack
        fail_msg = 'Stack suspend failed.'
        self.verify(
            10, self.heat_client.actions.suspend,
            4, fail_msg,
            'executing suspend stack action',
            stack.id
        )
        self.verify(
            60, self.wait_for_stack_status,
            5, fail_msg,
            'stack status becoming "SUSPEND_COMPLETE"',
            stack.id, 'SUSPEND_COMPLETE'
        )
        res = self.get_stack_resources(
            stack.id,
            key='resource_type', value='OS::Nova::Server'
        )
        self.verify_response_body_content(
            'SUSPEND_COMPLETE', res[0].resource_status,
            'Stack resource is not in "SUSPEND_COMPLETE" status.', 6
        )
        instance = self.compute_client.servers.get(res[0].physical_resource_id)
        self.verify_response_body_content(
            'SUSPENDED', instance.status,
            'Instance owned by stack is not in "SUSPENDED" status.', 7
        )

        # resume stack
        fail_msg = 'Stack resume failed.'
        self.verify(
            10, self.heat_client.actions.resume,
            8, fail_msg,
            'executing resume stack action',
            stack.id
        )
        self.verify(
            60, self.wait_for_stack_status,
            9, fail_msg,
            'stack status becoming "RESUME_COMPLETE"',
            stack.id, 'RESUME_COMPLETE'
        )
        res = self.get_stack_resources(
            stack.id,
            key='resource_type', value='OS::Nova::Server'
        )
        self.verify_response_body_content(
            'RESUME_COMPLETE', res[0].resource_status,
            'Stack resource is not in "RESUME_COMPLETE".', 10
        )
        instance = self.compute_client.servers.get(res[0].physical_resource_id)
        self.verify_response_body_content(
            'ACTIVE', instance.status,
            'Instance owned by stack is not in "ACTIVE" status.', 11
        )

        # stack check
        fail_msg = 'Stack check failed.'
        self.verify(
            10, self.heat_client.actions.check,
            12, fail_msg,
            'executing check stack action',
            stack.id
        )
        self.verify(
            60, self.wait_for_stack_status,
            13, fail_msg,
            'stack status becoming "CHECK_COMPLETE"',
            stack.id, 'CHECK_COMPLETE'
        )
        res = self.get_stack_resources(
            stack.id,
            key='resource_type', value='OS::Nova::Server'
        )
        self.verify_response_body_content(
            'CHECK_COMPLETE', res[0].resource_status,
            'Stack resource is not in "CHECK_COMPLETE" status', 14
        )
        instance = self.compute_client.servers.get(res[0].physical_resource_id)
        self.verify_response_body_content(
            'ACTIVE', instance.status,
            'Instance owned by stack is not in "ACTIVE" status', 15
        )

        # delete stack
        fail_msg = 'Cannot delete stack.'
        self.verify(
            10, self.heat_client.stacks.delete,
            16, fail_msg,
            'deleting stack',
            stack.id
        )
        self.verify(
            60, self.wait_for_stack_deleted,
            16, fail_msg,
            'deleting stack',
            stack.id
        )

    def test_actions(self):
        """Typical stack actions: create, delete, show details, etc.
        Target component: Heat

        Scenario:
            1. Create test flavor.
            2. Create a stack.
            3. Wait for the stack status to change to 'CREATE_COMPLETE'.
            4. Get the details of the created stack by its name.
            5. Get the resources list of the created stack.
            6. Get the details of the stack resource.
            7. Get the events list of the created stack.
            8. Get the details of the stack event.
            9. Get the stack template details.
            10. Delete the stack and wait for the stack to be deleted.
        Duration: 850 s.
        """

        self.check_image_exists()

        # create test flavor
        fail_msg = 'Test flavor was not created.'
        heat_flavor = self.verify(50, self.create_flavor, 1,
                                  fail_msg, 'flavor creation')

        # define stack parameters
        parameters = {
            'InstanceType': heat_flavor.name,
            'ImageId': self.config.compute.image_name
        }
        if 'neutron' in self.config.network.network_provider:
            parameters['network'] = self.private_net
            template = self.load_template(
                'heat_create_neutron_stack_template.yaml')
        else:
            template = self.load_template(
                'heat_create_nova_stack_template.yaml')

        # create stack
        fail_msg = 'Stack was not created properly.'
        stack = self.verify(20, self.create_stack, 2,
                            fail_msg, 'stack creation',
                            template, parameters=parameters)

        self.verify(600, self.wait_for_stack_status, 3,
                    fail_msg,
                    'stack status becoming "CREATE_COMPLETE"',
                    stack.id, 'CREATE_COMPLETE')

        # get stack details
        details = self.verify(20, self.heat_client.stacks.get, 4,
                              'Cannot retrieve stack details.',
                              'retrieving stack details',
                              stack.stack_name)

        fail_msg = 'Stack details contain incorrect values.'
        self.verify_response_body_content(details.id, stack.id,
                                          fail_msg, 4)
        self.verify_response_body_content(self.config.compute.image_name,
                                          details.parameters['ImageId'],
                                          fail_msg, 4)
        self.verify_response_body_content(details.stack_status,
                                          'CREATE_COMPLETE',
                                          fail_msg, 4)
        # get resources list
        fail_msg = "Cannot retrieve list of stack resources."
        resources = self.verify(10, self.heat_client.resources.list, 5,
                                fail_msg,
                                'retrieving list of stack resources',
                                stack.id)
        self.verify_response_body_content(len(resources), 1, fail_msg, 5)
        resource_id = resources[0].logical_resource_id
        self.verify_response_body_content('Server', resource_id,
                                          fail_msg, 5)

        # get resource details
        res_details = self.verify(10, self.heat_client.resources.get, 6,
                                  'Cannot retrieve stack resource details.',
                                  'retrieving stack resource details',
                                  stack.id, resource_id)

        fail_msg = 'Resource details contain incorrect values.'
        self.verify_response_body_content('CREATE_COMPLETE',
                                          res_details.resource_status,
                                          fail_msg, 6)
        self.verify_response_body_content('OS::Nova::Server',
                                          res_details.resource_type,
                                          fail_msg, 6)
        # get events list
        fail_msg = 'Cannot retrieve list of stack events.'
        events = self.verify(10, self.heat_client.events.list, 7,
                             fail_msg, 'retrieving list of stack events',
                             stack.id)
        self.verify_response_body_not_equal(0, len(events), fail_msg, 7)

        fail_msg = 'Event details contain incorrect values.'
        self.verify_response_body_content('Server',
                                          events[0].logical_resource_id,
                                          fail_msg, 7)
        # get event details
        event_id = events[0].id
        ev_details = self.verify(10, self.heat_client.events.get, 8,
                                 'Cannot retrieve stack event details.',
                                 'retrieving stack event details',
                                 stack.id, resource_id, event_id)

        fail_msg = 'Event details contain incorrect values.'
        self.verify_response_body_content(ev_details.id, event_id,
                                          fail_msg, 8)
        self.verify_response_body_content(ev_details.logical_resource_id,
                                          'Server', fail_msg, 8)

        # show template
        fail_msg = 'Cannot retrieve template of the stack.'
        act_tpl = self.verify(10, self.heat_client.stacks.template, 9,
                              fail_msg, 'retrieving stack template',
                              stack.id)

        check_content = lambda: ('InstanceType' in act_tpl['parameters'] and
                                 'Server' in act_tpl['resources'])
        self.verify(10, check_content, 9,
                    fail_msg, 'verifying template content')

        # delete stack
        fail_msg = 'Cannot delete stack.'
        self.verify(20, self.heat_client.stacks.delete, 10,
                    fail_msg, 'deleting stack',
                    stack.id)

        self.verify(100, self.wait_for_stack_deleted, 10,
                    fail_msg, 'deleting stack',
                    stack.id)

    def test_update(self):
        """Update stack actions: inplace, replace and update whole template
        Target component: Heat

        Scenario:
            1. Create test flavor.
            2. Create a stack.
            3. Wait for the stack status to change to 'CREATE_COMPLETE'.
            4. Change instance name, execute update stack in-place.
            5. Wait for the stack status to change to 'UPDATE_COMPLETE'.
            6. Check that instance name was changed.
            7. Create one more test flavor.
            8. Change instance flavor to just created and update stack
            (update replace).
            9. Wait for the stack status to change to 'UPDATE_COMPLETE'.
            10. Check that instance flavor was changed.
            11. Change stack template and update it.
            12. Wait for the stack status to change to 'UPDATE_COMPLETE'.
            13. Check that there are only two newly created stack instances.
            14. Delete the stack.
            15. Wait for the stack to be deleted.

        Duration: 950 s.
        """

        self.check_image_exists()

        # create test flavor
        fail_msg = 'Test flavor was not created.'
        heat_flavor = self.verify(50, self.create_flavor, 1,
                                  fail_msg, 'flavor creation')

        # define stack parameters
        parameters = {
            'InstanceType': heat_flavor.name,
            'ImageId': self.config.compute.image_name
        }
        if 'neutron' in self.config.network.network_provider:
            parameters['network'] = self.private_net
            template = self.load_template(
                'heat_create_neutron_stack_template.yaml')
        else:
            template = self.load_template(
                'heat_create_nova_stack_template.yaml')

        # create stack
        fail_msg = 'Stack was not created properly.'
        stack = self.verify(20, self.create_stack, 2,
                            fail_msg,
                            'stack creation',
                            template, parameters=parameters)

        self.verify(300, self.wait_for_stack_status, 3,
                    fail_msg,
                    'stack status becoming "CREATE_COMPLETE"',
                    stack.id, 'CREATE_COMPLETE')

        instances = self.get_stack_instances(stack.id)

        if not instances:
            self.fail('Failed step: 3. Instance for the {0} stack '
                      'was not created.'.format(stack.stack_name))

        fail_msg = 'Can not update stack.'

        # update inplace
        template = template.replace('name: ost1-test_heat',
                                    'name: ost1-test_updated')

        stack = self.verify(20, self.update_stack, 4,
                            fail_msg,
                            'updating stack, changing resource name',
                            stack.id,
                            template, parameters=parameters)

        self.verify(100, self.wait_for_stack_status, 5,
                    fail_msg,
                    'stack status becoming "UPDATE_COMPLETE"',
                    stack.id, 'UPDATE_COMPLETE')

        new_instance_name = self.compute_client.servers.get(
            instances[0]).name

        if new_instance_name != 'ost1-test_updated':
            self.fail('Failed step: 6 Stack update inplace was not '
                      'finished, instance name was not changed.')

        # creation of one more flavor, that will be used for 'update replace'
        flavor = self.verify(60, self.create_flavor, 7,
                             'Test flavor was not created.', 'flavor creation')

        # update replace
        parameters['InstanceType'] = flavor.name

        stack = self.verify(20, self.update_stack, 8,
                            fail_msg,
                            'updating stack, changing instance flavor',
                            stack.id,
                            template, parameters=parameters)

        self.verify(100, self.wait_for_stack_status, 9,
                    fail_msg,
                    'stack status becoming "UPDATE_COMPLETE"',
                    stack.id, 'UPDATE_COMPLETE')

        instances = self.get_stack_instances(stack.id)
        old_instance_id = instances[0]

        new_instance_flavor = self.compute_client.servers.get(
            instances[0]).flavor['id']

        if new_instance_flavor != flavor.id:
            self.fail('Failed step: 10. Stack update replace was not '
                      'finished, instance flavor was not changed.')

        # update the whole template: one old resource will be deleted and
        # two new resources will be created

        parameters = {
            'InstanceType': heat_flavor.name,
            'ImageId': self.config.compute.image_name
        }
        if 'neutron' in self.config.network.network_provider:
            parameters['network'] = self.private_net
            template = self.load_template(
                'heat_update_neutron_stack_template.yaml')
        else:
            template = self.load_template(
                'heat_update_nova_stack_template.yaml')

        stack = self.verify(20, self.update_stack, 11,
                            fail_msg,
                            'updating stack, changing template',
                            stack.id,
                            template, parameters=parameters)

        self.verify(180, self.wait_for_stack_status, 12,
                    fail_msg,
                    'stack status becoming "UPDATE_COMPLETE"',
                    stack.id, 'UPDATE_COMPLETE')

        instances = self.get_stack_instances(stack.id)

        if len(instances) != 2:
            self.fail('Failed step: 13. There are more then two expected '
                      'instances belonging test stack.')

        if old_instance_id in instances:
            self.fail('Failed step: 13. Previously create instance '
                      'was not deleted during stack update.')

        # delete stack
        fail_msg = 'Cannot delete stack.'
        self.verify(20, self.heat_client.stacks.delete, 14,
                    fail_msg, 'deleting stack',
                    stack.id)

        self.verify(100, self.wait_for_stack_deleted, 15,
                    fail_msg, 'deleting stack',
                    stack.id)

    def test_autoscaling(self):
        """Check stack autoscaling
        Target component: Heat

        Scenario:
            1. Create test flavor.
            2. Create a keypair.
            3. Save generated private key to file on Controller node.
            4. Create a security group.
            5. Create a stack.
            6. Wait for the stack status to change to 'CREATE_COMPLETE'.
            7. Create a floating IP.
            8. Assign the floating IP to the instance of the stack.
            9. Wait for instance is ready for load.
            10. Load the instance CPU to initiate the stack scaling up.
            11. Wait for the 2nd instance to be launched.
            12. Release the instance CPU to initiate the stack scaling down.
            13. Wait for the 2nd instance to be terminated.
            14. Delete the file with private key.
            15. Delete the stack.
            16. Wait for the stack to be deleted.

        Duration: 2200 s.
        """

        if not self.ceilometer_client:
            self.skipTest('This test can not be run in current configuration. '
                          'It checks Heat autoscaling using '
                          'Ceilometer resources, so Ceilometer '
                          'should be installed.')

        self.check_image_exists()

        # create test flavor
        fail_msg = 'Test flavor was not created.'
        heat_flavor = self.verify(50, self.create_flavor, 1,
                                  fail_msg, 'flavor creation')

        # creation of test keypair
        keypair = self.verify(10, self._create_keypair, 2,
                              'Keypair can not be created.',
                              'keypair creation',
                              self.compute_client)

        path_to_key = self.verify(10, self.save_key_to_file, 3,
                                  'Private key can not be saved to file.',
                                  'saving private key to the file',
                                  keypair.private_key)

        sec_group = self.verify(60, self._create_security_group, 4,
                                'Security group can not be created.',
                                'security group creation',
                                self.compute_client, 'ost1_test-sgroup')

        parameters = {
            'KeyName': keypair.name,
            'InstanceType': heat_flavor.name,
            'ImageId': self.config.compute.image_name,
            'SecurityGroup': sec_group.name
        }

        if 'neutron' in self.config.network.network_provider:
            parameters['Subnet'] = self.private_net
            template = self.load_template('heat_autoscaling_neutron.yaml')
        else:
            template = self.load_template('heat_autoscaling_nova.yaml')

        fail_msg = 'Stack was not created properly.'
        stack = self.verify(20, self.create_stack, 5,
                            fail_msg, 'stack creation',
                            template,
                            parameters=parameters)

        self.verify(600, self.wait_for_stack_status, 6,
                    fail_msg,
                    'stack status becoming "CREATE_COMPLETE"',
                    stack.id, 'CREATE_COMPLETE', 600, 15)

        reduced_stack_name = '{0}-{1}'.format(
            stack.stack_name[:2], stack.stack_name[-4:])

        instances = self.get_instances_by_name_mask(reduced_stack_name)

        if not instances:
            self.fail('Failed step: 6. Instance for the {0} stack '
                      'was not created.'.format(stack.stack_name))

        floating_ip = self.verify(10, self._create_floating_ip, 7,
                                  'Floating IP can not be created.',
                                  'floating IP creation')

        self.verify(20, self._assign_floating_ip_to_instance, 8,
                    'Floating IP can not be assigned.',
                    'assigning floating IP',
                    self.compute_client, instances[0], floating_ip)

        vm_connection = 'ssh -o StrictHostKeyChecking=no -i %s %s@%s' % (
            path_to_key, 'cirros', floating_ip.ip)

        self.verify(120, self.wait_for_vm_ready_for_load, 9,
                    'VM is not ready or connection can not be established',
                    'test script execution on VM',
                    vm_connection, 120, 15)

        self.verify(60, self.load_vm_cpu, 10,
                    'Cannot create a process to load VM CPU.',
                    'loading VM CPU',
                    vm_connection)

        self.verify(480,
                    self.wait_for_autoscaling, 11,
                    'Stack failed to launch the 2nd instance '
                    'per autoscaling alarm.',
                    'launching the new instance per autoscaling alarm',
                    len(instances) + 1, 480, 10, reduced_stack_name)

        self.verify(180, self.release_vm_cpu, 12,
                    'Cannot kill the process on VM to turn CPU load off.',
                    'turning off VM CPU load',
                    vm_connection)

        self.verify(480, self.wait_for_autoscaling, 13,
                    'Stack failed to terminate the 2nd instance '
                    'per autoscaling alarm.',
                    'terminating the 2nd instance per autoscaling alarm',
                    len(instances), 480, 10, reduced_stack_name)

        self.verify(10, self.delete_key_file, 14,
                    'The file with private key cannot be deleted.',
                    'deleting the file with private key',
                    path_to_key)

        self.verify(20, self.heat_client.stacks.delete, 15,
                    'Cannot delete stack.',
                    'deleting stack',
                    stack.id)

        self.verify(100, self.wait_for_stack_deleted, 16,
                    'Cannot delete stack.',
                    'deleting stack',
                    stack.id)

    def test_rollback(self):
        """Check stack rollback
        Target component: Heat

        Scenario:
            1. Create extra large flavor.
            2. Start stack creation with rollback enabled.
            3. Verify the stack appears with status 'CREATE_IN_PROGRESS'.
            4. Wait for the stack to be deleted in result of rollback after
               expiration of timeout defined in WaitHandle resource
               of the stack.
            5. Verify the instance of the stack has been deleted.

        Duration: 310 s.
        """
        self.check_image_exists()

        # create test flavor
        fail_msg = 'Test flavor was not created.'
        large_flavor = self.verify(50, self.create_flavor, 1,
                                   fail_msg, 'flavor creation', ram=1048576)

        parameters = {
            'InstanceType': large_flavor.name,
            'ImageId': self.config.compute.image_name
        }
        if 'neutron' in self.config.network.network_provider:
            parameters['network'] = self.private_net
            template = self.load_template(
                'heat_create_neutron_stack_template.yaml')
        else:
            template = self.load_template(
                'heat_create_nova_stack_template.yaml')
        fail_msg = 'Stack creation was not started.'
        stack = self.verify(60, self.create_stack, 2,
                            fail_msg, 'starting stack creation',
                            template,
                            disable_rollback=False,
                            parameters=parameters)

        self.verify_response_body_content('CREATE_IN_PROGRESS',
                                          stack.stack_status,
                                          fail_msg, 3)

        self.verify(180, self.wait_for_stack_deleted, 4,
                    'Rollback of the stack failed.',
                    'rolling back the stack after its creation failed',
                    stack.id)

        instances = self.get_instances_by_name_mask(stack.stack_name)

        self.verify(20, self.assertTrue, 5,
                    'The stack instance rollback failed.',
                    'verifying if the instance was rolled back',
                    len(instances) == 0)
