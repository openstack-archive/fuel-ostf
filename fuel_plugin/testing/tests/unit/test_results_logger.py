# -*- coding: utf-8 -*-

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

import mock

from fuel_plugin.ostf_adapter.logger import ResultsLogger
from fuel_plugin.testing.tests import base


@mock.patch.object(ResultsLogger, '_init_file_logger')
class TestResultsLogger(base.BaseUnitTest):

    def get_logger(self, **kwargs):
        options = {
            'testset': 'testset',
            'cluster_id': 1,
        }
        options.update(kwargs)
        return ResultsLogger(**options)

    def test_filename(self, minit_logger):
        logger = self.get_logger(testset='testset_name',
                                 cluster_id=99)
        expected = "cluster_99_testset_name.log"

        self.assertEqual(logger.filename, expected)

    def test_log_format_on_success(self, minit_logger):
        logger = self.get_logger()
        logger._logger = mock.Mock()

        logger.log_results(
            test_id='tests.successful.test', test_name='Successful test',
            status='SUCCESS', message='', traceback='')

        expected = 'SUCCESS Successful test (tests.successful.test)  '
        logger._logger.info.assert_called_once_with(expected)

    def test_log_format_on_fail(self, minit_logger):
        logger = self.get_logger()
        logger._logger = mock.Mock()

        logger.log_results(
            test_id='tests.failing.test', test_name='Failing test',
            status='FAIL', message='Message after fail', traceback='TRACEBACK')

        expected = ('FAIL Failing test (tests.failing.test) '
                    'Message after fail TRACEBACK')
        logger._logger.info.assert_called_once_with(expected)

    def test_log_format_on_error(self, minit_logger):
        logger = self.get_logger()
        logger._logger = mock.Mock()

        logger.log_results(
            test_id='tests.error.test', test_name='Error test',
            status='ERROR', message='Message after error',
            traceback="TRACEBACK")

        expected = ('ERROR Error test (tests.error.test) '
                    'Message after error TRACEBACK')
        logger._logger.info.assert_called_once_with(expected)
