#    Copyright 2014 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from nose import core


class SilentTestRunner(core.TextTestRunner):
    def run(self, test):
        """Overrides to provide plugin hooks and defer all output to
        the test result class.
        """
        result = self._makeResult()
        test(result)
        return result


class SilentTestProgram(core.TestProgram):
    def runTests(self):
        """Run Tests. Returns true on success, false on failure, and sets
        self.success to the same value.
        """
        self.testRunner = SilentTestRunner(stream=self.config.stream,
                                           verbosity=0,
                                           config=self.config)
        return self.testRunner.run(self.test).wasSuccessful()
