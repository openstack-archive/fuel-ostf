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


class HeatTest(heatmanager.HeatBaseTest):
    """Test class contains tests that check typical stack-related actions.
    Special requirements:
        1. Heat component should be installed.
    """

    @attr(type=["fuel", "smoke"])
    def test_manipulate_stack(self):
        """Check typical stack-related actions
        Target component: Heat

        Scenario:
            1. Create stack.
            2. Get details of the created stack by its name.
            3. Update stack.
            4. Delete stack.
        Duration: 60 s.
        """

        fail_msg = "Stack was not created properly."
        # create stack
        stack = self.verify(20, self.create_stack, 1,
                            fail_msg,
                            "stack creation",
                            self.heat_client)

        self.verify(100, self.wait_for_stack_status, 1,
                    fail_msg,
                    "stack status becoming 'CREATE_COMPLETE'",
                    stack.id, 'CREATE_COMPLETE')

        # get stack details
        stack_details = self.verify(20, self.heat_client.stacks.get, 2,
                                    "Cannot retrieve stack details.",
                                    "retrieving stack details",
                                    stack.stack_name)

        self.verify_response_body_content(
            stack_details.id,
            stack.id,
            "Stack details contain incorrect values.", 2)

        # update stack
        fail_msg = "Cannot update stack."
        stack = self.verify(20, self.update_stack, 3,
                            fail_msg,
                            "updating stack.",
                            self.heat_client, stack.id)

        self.verify(100, self.wait_for_stack_status, 3,
                    fail_msg,
                    "stack status becoming 'UPDATE_COMPLETE'",
                    stack.id, 'UPDATE_COMPLETE')

        # delete stack
        fail_msg = "Cannot delete stack."
        self.verify(20, self.heat_client.stacks.delete, 4,
                    fail_msg,
                    "volume deletion",
                    stack.id)

        self.verify(100, self.wait_for_stack_deleted, 4,
                    fail_msg,
                    "deleting stack",
                    stack.id)
