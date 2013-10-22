# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from nose.plugins.attrib import attr

from fuel_health import heatmanager


LOG = logging.getLogger(__name__)


class TestStackAction(heatmanager.HeatBaseTest):
    """
    Test class verifies that stack can be created, updated and deleted
    Special requirements:
        1. Heat component should be installed.
    """

    @attr(type=["fuel", "smoke"])
    def test_stack(self):
        """Create stack, check its details, then update and delete Heat stack
        Target component: Heat

        Scenario:
            1. Create stack.
            2. Wait for stack status to become 'CREATE_COMPLETE'.
            3. Get details of the created stack by its name.
            4. Update stack.
            5. Wait for stack to be updated.
            6. Delete stack.
            7. Wait for stack to be deleted.
        Duration: 600 s.

        Deployment tags: Heat
        """

        fail_msg = "Stack was not created properly."
        # create stack
        stack = self.verify(100, self.create_stack, 1,
                            fail_msg,
                            "stack creation",
                            self.heat_client)

        self.verify(100, self.wait_for_stack_status, 2,
                    fail_msg,
                    "stack status becoming 'CREATE_COMPLETE'",
                    stack.id, 'CREATE_COMPLETE')

        # get stack details
        details = self.verify(100, self.heat_client.stacks.get, 3,
                              "Cannot retrieve stack details.",
                              "retrieving stack details",
                              stack.stack_name)

        fail_msg = "Stack details contain incorrect values."
        self.verify_response_body_content(
            details.id, stack.id,
            fail_msg, 3)

        self.verify_response_body_content(
            self.config.compute.image_name, details.parameters['ImageId'],
            fail_msg, 3)

        self.verify_response_body_content(
            details.stack_status, 'CREATE_COMPLETE',
            fail_msg, 3)

        # update stack
        fail_msg = "Cannot update stack."
        stack = self.verify(100, self.update_stack, 4,
                            fail_msg,
                            "updating stack.",
                            self.heat_client, stack.id)

        self.verify(100, self.wait_for_stack_status, 5,
                    fail_msg,
                    "stack status becoming 'UPDATE_COMPLETE'",
                    stack.id, 'UPDATE_COMPLETE')

        # delete stack
        fail_msg = "Cannot delete stack."
        self.verify(100, self.heat_client.stacks.delete, 6,
                    fail_msg,
                    "deleting stack",
                    stack.id)

        self.verify(100, self.wait_for_stack_deleted, 7,
                    fail_msg,
                    "deleting stack",
                    stack.id)
