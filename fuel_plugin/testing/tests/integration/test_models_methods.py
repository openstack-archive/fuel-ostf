#    Copyright 2015 Mirantis, Inc.
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

import six

from fuel_plugin.testing.tests import base

from fuel_plugin.ostf_adapter import mixins
from fuel_plugin.ostf_adapter.storage.models import Test
from fuel_plugin.ostf_adapter.storage.models import TestRun


class TestModelTestMethods(base.BaseIntegrationTest):

    def setUp(self):
        super(TestModelTestMethods, self).setUp()

        self.discovery()

        self.test_set_id = 'general_test'
        self.cluster_id = 1

        self.mock_api_for_cluster(self.cluster_id)

        mixins.discovery_check(self.session, self.cluster_id)
        self.session.flush()

        self.test = self.session.query(Test)\
            .filter_by(test_set_id=self.test_set_id)\
            .first()

        self.test_run = TestRun.add_test_run(
            self.session,
            self.test.test_set_id,
            self.cluster_id,
            status='running',
            tests=[self.test.name]
        )
        self.session.flush()

    @property
    def test_to_check(self):
        return self.session.query(Test)\
            .filter_by(test_run_id=self.test_run.id)\
            .filter_by(name=self.test.name)\
            .first()

    def check_model_obj_attrs(self, obj, attrs):
        for attr_name, attr_val in six.iteritems(attrs):
            self.assertEqual(attr_val, getattr(obj, attr_name))

    def test_add_result(self):
        expected_data = {
            'message': 'test_message',
            'status': 'error',
            'time_taken': 10.4
        }

        Test.add_result(self.session,
                        self.test_run.id,
                        self.test.name,
                        expected_data)

        self.check_model_obj_attrs(self.test_to_check, expected_data)

    def test_update_running_tests_default_status(self):
        Test.update_running_tests(self.session,
                                  self.test_run.id)

        self.assertEqual(self.test_to_check.status, 'stopped')

    def test_update_running_tests_with_status(self):
        expected_status = 'success'
        Test.update_running_tests(self.session,
                                  self.test_run.id,
                                  status=expected_status)

        self.assertEqual(self.test_to_check.status, expected_status)

    def test_update_only_running_tests(self):
        # the method should update only running tests
        expected_status = 'error'
        Test.add_result(self.session, self.test_run.id, self.test.name,
                        {'status': expected_status})

        Test.update_running_tests(self.session, self.test_run.id)

        # check that status of test is not updated to 'stopped'
        self.assertEqual(self.test_to_check.status, expected_status)

    def test_update_test_run_tests_default_status(self):
        # set 'time_taken' attribute to non-null value
        Test.add_result(self.session, self.test_run.id, self.test.name,
                        {'time_taken': 10.4})

        Test.update_test_run_tests(self.session, self.test_run.id,
                                   [self.test.name])

        expected_attrs = {
            'status': 'wait_running',
            'time_taken': None
        }

        self.check_model_obj_attrs(self.test_to_check, expected_attrs)

    def test_properly_copied_test(self):
        new_test = self.test.copy_test(self.test_run, predefined_tests=[])

        copied_attrs_list = [
            'name',
            'title',
            'description',
            'duration',
            'message',
            'traceback',
            'step',
            'time_taken',
            'meta',
            'deployment_tags',
            'available_since_release',
            'test_set_id',
        ]
        attrs = {}
        for attr_name in copied_attrs_list:
            attrs[attr_name] = getattr(self.test, attr_name)

        self.check_model_obj_attrs(new_test, attrs)

        self.assertEqual(new_test.test_run_id, self.test_run.id)
        self.assertEqual(new_test.status, 'wait_running')

    def test_copy_test_with_predefined_list(self):
        predefined_tests_names = ['some_other_test']
        new_test = self.test.copy_test(self.test_run,
                                       predefined_tests_names)

        self.assertEqual(new_test.status, 'disabled')
