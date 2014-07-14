# Copyright 2013 Mirantis, Inc.
#
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
    """
    Test class verifies Heat API calls, rollback and autoscaling use-cases.
    Special requirements:
        1. Fedora-17 image with pre-installed cfntools and cloud-init packages
           should be imported.
    """
    def setUp(self):
        super(HeatSmokeTests, self).setUp()
        if not self.config.compute.compute_nodes:
            self.skipTest('There are no compute nodes')
        self.instance = []

    def test_actions(self):
        """Typical stack actions: create, update, delete, show details, etc.
        Target component: Heat

        Scenario:
            1. Create a stack.
            2. Wait for the stack status to change to 'CREATE_COMPLETE'.
            3. Get the details of the created stack by its name.
            4. Get the resources list of the created stack.
            5. Get the details of the stack resource.
            6. Get the events list of the created stack.
            7. Get the details of the stack event.
            8. Update the stack.
            9. Wait for the stack to update.
            10. Get the stack template details.
            11. Get the resources list of the updated stack.
            12. Delete the stack.
            13. Wait for the stack to be deleted.
        Duration: 640 s.
        """
        self.check_image_exists()
        parameters = {
            "InstanceType": self.testvm_flavor.name,
            "ImageId": self.config.compute.image_name
        }
        if 'neutron' in self.config.network.network_provider:
            parameters["Subnet"] = self._get_subnet_id()
            parameters['network'] = self._get_net_uuid()[0]
            template = self._load_template(
                'heat_create_neutron_stack_template.yaml')
        else:
            template = self._load_template(
                'heat_create_nova_stack_template.yaml')

        fail_msg = "Stack was not created properly."
        # create stack
        stack = self.verify(20, self._create_stack, 1,
                            fail_msg,
                            "stack creation",
                            self.heat_client,
                            template,
                            parameters=parameters)

        self.verify(600, self._wait_for_stack_status, 2,
                    fail_msg,
                    "stack status becoming 'CREATE_COMPLETE'",
                    stack.id, 'CREATE_COMPLETE')

        # get stack details
        details = self.verify(20, self.heat_client.stacks.get, 3,
                              "Cannot retrieve stack details.",
                              "retrieving stack details",
                              stack.stack_name)

        fail_msg = "Stack details contain incorrect values."
        self.verify_response_body_content(details.id, stack.id,
                                          fail_msg, 3)
        self.verify_response_body_content(self.config.compute.image_name,
                                          details.parameters['ImageId'],
                                          fail_msg, 3)
        self.verify_response_body_content(details.stack_status,
                                          'CREATE_COMPLETE',
                                          fail_msg, 3)
        # get resources list
        fail_msg = "Cannot retrieve list of stack resources."
        resources = self.verify(10, self.heat_client.resources.list, 4,
                                fail_msg,
                                "retrieving list of stack resources",
                                stack.id)
        self.verify_response_body_content(len(resources), 1, fail_msg, 4)
        resource_id = resources[0].logical_resource_id
        self.verify_response_body_content("Server", resource_id,
                                          fail_msg, 4)

        # get resource details
        res_details = self.verify(10, self.heat_client.resources.get, 5,
                                  "Cannot retrieve stack resource details.",
                                  "retrieving stack resource details",
                                  stack.id, resource_id)

        fail_msg = "Resource details contain incorrect values."
        self.verify_response_body_content("CREATE_COMPLETE",
                                          res_details.resource_status,
                                          fail_msg, 5)
        self.verify_response_body_content("OS::Nova::Server",
                                          res_details.resource_type,
                                          fail_msg, 5)
        # get events list
        fail_msg = "Cannot retrieve list of stack events."
        events = self.verify(10, self.heat_client.events.list, 6,
                             fail_msg, "retrieving list of stack events",
                             stack.id)
        self.verify_response_body_not_equal(0, len(events), fail_msg, 6)

        fail_msg = "Event details contain incorrect values."
        self.verify_response_body_content("Server",
                                          events[0].logical_resource_id,
                                          fail_msg, 6)
        # get event details
        event_id = events[0].id
        ev_details = self.verify(10, self.heat_client.events.get, 7,
                                 "Cannot retrieve stack event details.",
                                 "retrieving stack event details",
                                 stack.id, resource_id, event_id)

        fail_msg = "Event details contain incorrect values."
        self.verify_response_body_content(ev_details.id, event_id,
                                          fail_msg, 7)
        self.verify_response_body_content(ev_details.logical_resource_id,
                                          "Server", fail_msg, 7)

        # update stack
        template = template.replace('Name: ost1-test_heat',
                                    'Name: ost1-test_updated')
        fail_msg = "Cannot update stack."
        stack = self.verify(20, self._update_stack, 8,
                            fail_msg,
                            "updating stack.",
                            self.heat_client, stack.id,
                            template,
                            parameters=parameters)
        self.verify(100, self._wait_for_stack_status, 9,
                    fail_msg,
                    "stack status becoming 'UPDATE_COMPLETE'",
                    stack.id, 'UPDATE_COMPLETE')

        # show template
        fail_msg = "Cannot retrieve template of the stack."
        act_tpl = self.verify(10, self.heat_client.stacks.template,
                              10,
                              fail_msg,
                              "retrieving stack template",
                              stack.id)

        check_content = lambda: ("InstanceType" in act_tpl["parameters"] and
                                 "Server" in act_tpl["resources"])
        self.verify(10, check_content, 10,
                    fail_msg, "verifying template content")

        # get updated resources list
        resources = self.verify(10, self.heat_client.resources.list, 11,
                                "Cannot retrieve list of stack resources.",
                                "retrieving list of stack resources",
                                stack.id)
        resource_id = resources[0].logical_resource_id
        self.verify_response_body_content("Server", resource_id,
                                          fail_msg, 11)

        # delete stack
        fail_msg = "Cannot delete stack."
        self.verify(20, self.heat_client.stacks.delete, 12,
                    fail_msg,
                    "deleting stack",
                    stack.id)

        self.verify(100, self._wait_for_stack_deleted, 13,
                    fail_msg,
                    "deleting stack",
                    stack.id)

    def test_autoscaling(self):
        """Check stack autoscaling
        Target component: Heat

        Scenario:
            1. Image with cfntools package should be imported.
            2. Create a flavor.
            3. Create a keypair.
            4. Save generated private key to file on Controller node.
            5. Create a security group.
            6. Create a stack.
            7. Wait for the stack status to change to 'CREATE_COMPLETE'.
            8. Create a floating ip.
            9. Assign the floating ip to the instance of the stack.
            10. Wait for cloud_init procedure to be completed on the instance.
            11. Load the instance CPU to initiate the stack scaling up.
            12. Wait for the 2nd instance to be launched.
            13. Release the instance CPU to initiate the stack scaling down.
            14. Wait for the 2nd instance to be terminated.
            15. Delete the file with private key.
            16. Delete the stack.
            17. Wait for the stack to be deleted.
        Duration: 2600 s.
        """
        image_name = "F17-x86_64-cfntools"
        fail_msg = ("Image with cfntools package wasn't "
                    "imported into Glance, please check "
                    "http://docs.mirantis.com/openstack/fuel/fuel"
                    "-5.0/user-guide.html#platform-tests-description")

        image_available = self.verify(10, self._find_heat_image, 1,
                                      fail_msg,
                                      "checking if %s image is registered "
                                      "in Glance" % image_name,
                                      image_name)

        self.verify_response_true(image_available,
                                  "Step 1 failed: %s." % fail_msg)

        flavor = self.verify(10, self._create_flavors, 2,
                             "Flavor can not be created.",
                             "flavor creation",
                             self.compute_client, 382, 12)

        keypair = self.verify(10, self._create_keypair, 3,
                              'Keypair can not be created.',
                              'keypair creation',
                              self.compute_client)

        path_to_key = self.verify(10, self._save_key_to_file, 4,
                                  "Private key can not be saved to file.",
                                  "saving private key to the file",
                                  keypair.private_key)

        sec_group = self.verify(10, self._create_security_group, 5,
                                'Security group can not be created.',
                                'security group creation',
                                self.compute_client, 'ost1_test-sgroup')

        parameters = {
            "KeyName": keypair.name,
            "InstanceType": flavor.name,
            "ImageId": image_name,
            "SecurityGroup": sec_group.name
        }
        if 'neutron' in self.config.network.network_provider:
            parameters['Subnet'] = self._get_subnet_id()
            template = self._load_template('heat_autoscaling_template.yaml')
        else:
            template = self._load_template('heat_autoscale_nova.yaml')

        # create stack
        fail_msg = "Stack was not created properly."
        stack = self.verify(20, self._create_stack, 6,
                            fail_msg, "stack creation",
                            self.heat_client, template,
                            parameters=parameters)

        self.verify(600, self._wait_for_stack_status, 7,
                    fail_msg,
                    "stack status becoming 'CREATE_COMPLETE'",
                    stack.id, 'CREATE_COMPLETE', 600, 15)

        reduced_stack_name = '{0}-{1}'.format(
            stack.stack_name[:2], stack.stack_name[-4:])

        # find just created instance
        instance_list = self.compute_client.servers.list()
        LOG.info('servers list is {0}'.format(instance_list))
        LOG.info('expected img_name starts with {0}'.format(
            reduced_stack_name))

        for i in instance_list:
            details = self.compute_client.servers.get(server=i)
            LOG.info('instance name is {0}'.format(details.name))
            if details.name.startswith(reduced_stack_name):
                self.instance.append(i)

        if not self.instance:
            self.fail("Failed step: 7 Instance for the {0} stack "
                      "was not created.".format(self.instance))

        floating_ip = self.verify(10, self._create_floating_ip, 8,
                                  "Floating IP can not be created.",
                                  'floating IP creation')

        self.verify(10, self._assign_floating_ip_to_instance, 9,
                    "Floating IP can not be assigned.",
                    'assigning floating IP',
                    self.compute_client, self.instance[0], floating_ip)

        vm_connection = "ssh -o StrictHostKeyChecking=no -i %s %s@%s" % (
            path_to_key, "ec2-user", floating_ip.ip)

        self.verify(1000, self._wait_for_cloudinit, 10,
                    "Cloud-init script cannot finish within timeout.",
                    "cloud-init script execution on VM",
                    vm_connection, 1000, 15)

        self.verify(60, self._load_vm_cpu, 11,
                    "Cannot create a process to load VM CPU.",
                    "loading VM CPU",
                    vm_connection)

        self.verify(300,
                    self._wait_for_autoscaling, 12,
                    "Stack failed to launch the 2nd instance "
                    "per autoscaling alarm.",
                    "launching the new instance per autoscaling alarm",
                    len(self.instance) + 1, 300, 10, reduced_stack_name)

        self.verify(180, self._release_vm_cpu, 13,
                    "Cannot kill the process on VM to turn CPU load off.",
                    "turning off VM CPU load",
                    vm_connection)

        self.verify(300, self._wait_for_autoscaling, 14,
                    "Stack failed to terminate the 2nd instance "
                    "per autoscaling alarm.",
                    "terminating the 2nd instance per autoscaling alarm",
                    len(self.instance), 300, 10, reduced_stack_name)

        # delete private key file
        self.verify(10, self._delete_key_file, 15,
                    "The file with private key cannot be deleted.",
                    "deleting the file with private key",
                    path_to_key)

        fail_msg = "Cannot delete stack."
        self.verify(20, self.heat_client.stacks.delete, 16,
                    fail_msg,
                    "deleting stack",
                    stack.id)

        self.verify(100, self._wait_for_stack_deleted, 17,
                    fail_msg,
                    "deleting stack",
                    stack.id)

    def test_rollback(self):
        """Check stack rollback
        Target component: Heat

        Scenario:
            1. Start stack creation with rollback enabled.
            2. Verify the stack appears with status 'CREATE_IN_PROGRESS'.
            3. Wait for the stack to be deleted in result of rollback after
               expiration of timeout defined in WaitHandle resource
               of the stack.
            4. Verify the instance of the stack has been deleted.
        Duration: 140 s.
        """
        self.check_image_exists()

        parameters = {
            "InstanceType": "non-exists",
            "ImageId": self.config.compute.image_name
        }
        if 'neutron' in self.config.network.network_provider:
            parameters['Subnet'] = self._get_subnet_id()
            parameters['network'] = self._get_net_uuid()[0]
            template = self._load_template(
                'heat_create_neutron_stack_template.yaml')
        else:
            template = self._load_template(
                'heat_create_nova_stack_template.yaml')
        fail_msg = "Stack creation was not started."
        stack = self.verify(20, self._create_stack, 1,
                            fail_msg, "starting stack creation",
                            self.heat_client, template,
                            disable_rollback=False,
                            parameters=parameters)

        self.verify_response_body_content("CREATE_IN_PROGRESS",
                                          stack.stack_status,
                                          fail_msg, 2)

        self.verify(100, self._wait_for_stack_deleted, 3,
                    "Rollback of the stack failed.",
                    "rolling back the stack after its creation failed",
                    stack.id)

        instances = [i for i in self.compute_client.servers.list()
                     if i.name.startswith(stack.stack_name)]
        self.verify(20, self.assertTrue, 4,
                    "The stack instance rollback failed.",
                    "verifying if the instance was rolled back",
                    len(instances) == 0)
