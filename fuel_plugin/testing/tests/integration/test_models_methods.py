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

import datetime
import six

import mock

from fuel_plugin.testing.tests import base

from fuel_plugin.ostf_adapter import mixins

from fuel_plugin.ostf_adapter.storage import models


class TestModelTestMethods(base.BaseIntegrationTest):

    test_set_id = 'general_test'
    cluster_id = 1

    def setUp(self):
        super(TestModelTestMethods, self).setUp()

        self.discovery()

        self.mock_api_for_cluster(self.cluster_id)

        mixins.discovery_check(self.session, self.cluster_id)
        self.session.flush()

        self.test_obj = self.session.query(models.Test)\
            .filter_by(test_set_id=self.test_set_id)\
            .first()

        self.test_run = models.TestRun.add_test_run(
            self.session,
            self.test_obj.test_set_id,
            self.cluster_id,
            status='running',
            tests=[self.test_obj.name]
        )
        self.session.flush()

    @property
    def test_to_check(self):
        return self.session.query(models.Test)\
            .filter_by(test_run_id=self.test_run.id)\
            .filter_by(name=self.test_obj.name)\
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

        models.Test.add_result(self.session,
                               self.test_run.id,
                               self.test_obj.name,
                               expected_data)

        self.check_model_obj_attrs(self.test_to_check, expected_data)

    def test_update_running_tests_default_status(self):
        models.Test.update_running_tests(self.session,
                                         self.test_run.id)

        self.assertEqual(self.test_to_check.status, 'stopped')

    def test_update_running_tests_with_status(self):
        expected_status = 'success'

        models.Test.update_running_tests(self.session,
                                         self.test_run.id,
                                         status=expected_status)

        self.assertEqual(self.test_to_check.status, expected_status)

    def test_update_only_running_tests(self):
        # the method should update only running tests
        expected_status = 'error'
        models.Test.add_result(self.session, self.test_run.id,
                               self.test_obj.name,
                               {'status': expected_status})

        models.Test.update_running_tests(self.session, self.test_run.id)

        # check that status of test is not updated to 'stopped'
        self.assertEqual(self.test_to_check.status, expected_status)

    def test_update_test_run_tests_default_status(self):
        models.Test.add_result(self.session, self.test_run.id,
                               self.test_obj.name,
                               {'time_taken': 10.4})

        models.Test.update_test_run_tests(self.session, self.test_run.id,
                                          [self.test_obj.name])

        expected_attrs = {
            'status': 'wait_running',
            'time_taken': None
        }

        self.check_model_obj_attrs(self.test_to_check, expected_attrs)

    def test_properly_copied_test(self):
        new_test = self.test_obj.copy_test(self.test_run, predefined_tests=[])

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
            attrs[attr_name] = getattr(self.test_obj, attr_name)

        self.check_model_obj_attrs(new_test, attrs)

        self.assertEqual(new_test.test_run_id, self.test_run.id)
        self.assertEqual(new_test.status, 'wait_running')

    def test_copy_test_with_predefined_list(self):
        predefined_tests_names = ['some_other_test']
        new_test = self.test_obj.copy_test(self.test_run,
                                           predefined_tests_names)

        self.assertEqual(new_test.status, 'disabled')


class TestModelTestSetMethods(base.BaseIntegrationTest):

    test_set_id = 'general_test'

    def setUp(self):
        super(TestModelTestSetMethods, self).setUp()
        self.discovery()

    def test_get_test_set(self):
        self.assertIsNotNone(
            models.TestSet.get_test_set(
                self.session,
                self.test_set_id
            )
        )
        self.assertIsNone(
            models.TestSet.get_test_set(
                self.session,
                'fake_test'
            )
        )

    def test_frontend_property(self):
        test_set = self.session.query(models.TestSet)\
            .filter_by(id=self.test_set_id)\
            .first()
        expected = {'id': test_set.id, 'name': test_set.description}
        self.assertEqual(expected, test_set.frontend)


class TestModelTestRunMethods(base.BaseIntegrationTest):

    test_set_id = 'general_test'
    cluster_id = 1

    def setUp(self):
        super(TestModelTestRunMethods, self).setUp()
        self.discovery()

        self.mock_api_for_cluster(self.cluster_id)
        mixins.discovery_check(self.session, self.cluster_id)
        self.session.flush()

    def check_enabled(self, expected_test_names, test_run_tests):
        enabled_tests = [
            test.name for test in test_run_tests
            if test.status == 'wait_running'
        ]

        self.assertItemsEqual(expected_test_names, enabled_tests)

    def test_add_test_run(self):
        test_run = models.TestRun.add_test_run(
            self.session, self.test_set_id,
            self.cluster_id
        )

        for attr in ('test_set_id', 'cluster_id'):
            self.assertEqual(getattr(self, attr), getattr(test_run, attr))

        # default status for newly created test_run is 'running'
        self.assertEqual(test_run.status, 'running')

        unassigned_tests = self.session.query(models.Test)\
            .filter_by(test_set_id=self.test_set_id)\
            .filter_by(test_run_id=None)

        test_names_from_test_set = [
            test.name for test in unassigned_tests
        ]
        test_names_from_test_run = [
            test.name for test in test_run.tests
        ]
        self.assertItemsEqual(test_names_from_test_run,
                              test_names_from_test_set)

    def test_add_test_run_non_default_status(self):
        expected_status = 'finished'
        test_run = models.TestRun.add_test_run(
            self.session, self.test_set_id,
            self.cluster_id, status=expected_status
        )
        self.assertEqual(test_run.status, expected_status)

    def test_add_test_run_with_predefined_tests(self):
        expected_test_names = [
            test.name for test in
            self.session.query(models.Test)
                .filter_by(test_set_id=self.test_set_id)
                .filter_by(test_run_id=None)
        ][:3]

        test_run = models.TestRun.add_test_run(
            self.session, self.test_set_id,
            self.cluster_id, tests=expected_test_names
        )
        self.check_enabled(expected_test_names, test_run.tests)

    def test_add_test_run_tests_from_another_test_set_in_predefined(self):
        expected_test_names = [
            test.name for test in
            self.session.query(models.Test)
                .filter_by(test_set_id=self.test_set_id)
                .filter_by(test_run_id=None)
        ][:3]

        additional_test = self.session.query(models.Test)\
            .filter_by(test_set_id='stopped_test')\
            .first()

        tests = expected_test_names + [additional_test]
        test_run = models.TestRun.add_test_run(
            self.session, self.test_set_id,
            self.cluster_id,
            tests=tests
        )

        self.assertNotIn(
            additional_test.name,
            [test.name for test in test_run.tests]
        )
        self.check_enabled(expected_test_names, test_run.tests)

    def test_update_testrun_not_finished_status(self):
        test_run = models.TestRun.add_test_run(
            self.session, self.test_set_id,
            self.cluster_id
        )

        expected_status = 'stopped'
        test_run.update(expected_status)

        self.assertEqual(test_run.status, expected_status)
        self.assertIsNone(test_run.ended_at)

    @mock.patch('fuel_plugin.ostf_adapter.storage.models.datetime')
    def test_update_testrun_with_finished_status(self, mock_dt):
        expected_status = 'finished'
        expected_date = datetime.datetime.utcnow()
        mock_dt.datetime.utcnow.return_value = expected_date

        test_run = models.TestRun.add_test_run(
            self.session, self.test_set_id,
            self.cluster_id
        )

        test_run.update(expected_status)

        self.assertEqual(test_run.status, expected_status)
        self.assertEqual(test_run.ended_at, expected_date)

    def test_get_last_test_run(self):
        test_run = models.TestRun.add_test_run(
            self.session, self.test_set_id,
            self.cluster_id
        )

        last_test_run = models.TestRun.get_last_test_run(
            self.session, self.test_set_id, self.cluster_id)

        self.assertEqual(test_run, last_test_run)

    @mock.patch('fuel_plugin.ostf_adapter.storage.models.nose_plugin')
    def test_start_testrun(self, nose_plugin_mock):
        test_set = self.session.query(models.TestSet)\
            .filter_by(id=self.test_set_id).one()

        kwargs = {
            'session': self.session,
            'test_set': test_set,
            'metadata': {'cluster_id': self.cluster_id},
            'dbpath': 'fake_db_path',
            'token': 'fake_token',
            'tests': None,
        }

        plugin_inst_mock = mock.Mock()
        nose_plugin_mock.get_plugin = mock.Mock(
            return_value=plugin_inst_mock
        )

        with mock.patch.object(
                models.TestRun, 'is_last_running',
                new=mock.Mock(return_value=True)) as is_last_run_mock:

            frontend = models.TestRun.start(
                **kwargs
            )

        added_test_run = self.session.query(models.TestRun)\
            .first()
        self.assertEqual(frontend, added_test_run.frontend)

        nose_plugin_mock.get_plugin.called_once_with(test_set.driver)
        is_last_run_mock.called_once_with(
            self.session,
            test_set.id,
            self.cluster_id
        )
        plugin_inst_mock.run.called_once_with(
            added_test_run, test_set, kwargs['dbpath'], None, kwargs['token']
        )

    @mock.patch('fuel_plugin.ostf_adapter.storage.models.nose_plugin')
    def test_start_test_run_already_running(self, nose_plugin_mock):
        test_set = self.session.query(models.TestSet)\
            .filter_by(id=self.test_set_id).one()

        kwargs = {
            'session': self.session,
            'test_set': test_set,
            'metadata': {'cluster_id': self.cluster_id},
            'dbpath': 'fake_db_path',
            'token': 'fake_token',
            'tests': None,
        }

        with mock.patch.object(
                models.TestRun, 'is_last_running',
                new=mock.Mock(return_value=False)):

            frontend = models.TestRun.start(
                **kwargs
            )

        added_test_run = self.session.query(models.TestRun)\
            .first()
        self.assertIsNone(added_test_run)

        self.assertEqual(frontend, {})

    @mock.patch('fuel_plugin.ostf_adapter.storage.models.nose_plugin')
    def test_restart_test_run(self, nose_plugin_mock):
        test_run = models.TestRun.add_test_run(
            self.session, self.test_set_id,
            self.cluster_id
        )

        kwargs = {
            'session': self.session,
            'ostf_os_access_creds': [],
            'dbpath': 'fake_db_path',
            'token': 'fake_token',
            'tests': 'fake_tests'
        }

        plugin_inst_mock = mock.Mock()
        nose_plugin_mock.get_plugin = mock.Mock(
            return_value=plugin_inst_mock
        )

        with mock.patch.object(
                models.TestRun, 'is_last_running',
                new=mock.Mock(return_value=True)) as is_last_run_mock:

            with mock.patch.object(
                    models.Test, 'update_test_run_tests') as update_tests_mock:
                frontend = test_run.restart(**kwargs)

        self.assertEqual(test_run.frontend, frontend)
        self.assertEqual(test_run.status, 'running')

        is_last_run_mock.called_once_with(
            self.session,
            test_run.test_set_id,
            test_run.cluster_id
        )
        nose_plugin_mock.get_plugin.assert_called_once_with(
            test_run.test_set.driver
        )
        update_tests_mock.assert_called_once_with(
            self.session, test_run.id, kwargs['tests']
        )
        plugin_inst_mock.run.assert_called_once_with(
            test_run, test_run.test_set, kwargs['dbpath'],
            kwargs['ostf_os_access_creds'], kwargs['tests'],
            token=kwargs['token']
        )

    def test_run_restart_is_running(self):
        test_run = models.TestRun.add_test_run(
            self.session, self.test_set_id,
            self.cluster_id
        )

        kwargs = {
            'session': self.session,
            'ostf_os_access_creds': [],
            'dbpath': 'fake_db_path',
            'token': 'fake_token',
            'tests': 'fake_tests'
        }

        with mock.patch.object(
                models.TestRun, 'is_last_running',
                new=mock.Mock(return_value=False)) as is_last_run_mock:
            frontend = test_run.restart(**kwargs)

        is_last_run_mock.called_once_with(
            self.session,
            test_run.test_set_id,
            test_run.cluster_id
        )
        self.assertEqual(frontend, {})

    @mock.patch('fuel_plugin.ostf_adapter.storage.models.nose_plugin')
    def test_stop_test_run(self, nose_plugin_mock):
        test_run = models.TestRun.add_test_run(
            self.session, self.test_set_id,
            self.cluster_id
        )

        plugin_inst_mock = mock.Mock()
        kill_mock = mock.Mock(return_value=True)
        plugin_inst_mock.kill = kill_mock
        nose_plugin_mock.get_plugin = mock.Mock(
            return_value=plugin_inst_mock
        )

        with mock.patch.object(
                models.Test, 'update_running_tests') as update_tests_mock:
            frontend = test_run.stop(self.session)

        self.assertEqual(frontend, test_run.frontend)

        nose_plugin_mock.get_plugin.assert_called_once_with(
            test_run.test_set.driver
        )
        kill_mock.assert_called_once_with(test_run)
        update_tests_mock.assert_called_once_with(
            self.session, test_run.id, status='stopped'
        )

    def test_is_last_running(self):
        is_last_running = models.TestRun.is_last_running(
            self.session, self.test_set_id, self.cluster_id
        )
        self.assertTrue(is_last_running)

        test_run = models.TestRun.add_test_run(
            self.session, self.test_set_id,
            self.cluster_id
        )
        is_last_running = models.TestRun.is_last_running(
            self.session, self.test_set_id, self.cluster_id
        )
        self.assertFalse(is_last_running)

        test_run.status = 'finished'
        is_last_running = models.TestRun.is_last_running(
            self.session, self.test_set_id, self.cluster_id
        )
        self.assertTrue(is_last_running)
