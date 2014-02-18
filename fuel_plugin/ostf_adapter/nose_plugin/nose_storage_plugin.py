#    Copyright 2013 Mirantis, Inc.
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

from time import time
import logging
import os
from nose import plugins
from pecan import conf
import unittest2

from fuel_plugin.ostf_adapter.nose_plugin import nose_utils
from fuel_plugin.ostf_adapter.storage import models, engine


LOG = logging.getLogger(__name__)


class InterruptTestRunException(KeyboardInterrupt):
    ''' Current class exception is used for cleanup action
    as KeyboardInterrupt is the only exception that is reraised by
    unittest (and nose correspondingly) into outside environment
    '''
    pass


class StoragePlugin(plugins.Plugin):
    enabled = True
    name = 'storage'
    score = 15000

    def __init__(
            self, test_run_id, cluster_id):
        self.test_run_id = test_run_id
        self.cluster_id = cluster_id
        super(StoragePlugin, self).__init__()
        self._start_time = None

        self.session = engine.get_session()

    def options(self, parser, env=os.environ):
        env['NAILGUN_HOST'] = str(conf.nailgun.host)
        env['NAILGUN_PORT'] = str(conf.nailgun.port)
        if self.cluster_id:
            env['CLUSTER_ID'] = str(self.cluster_id)

    def configure(self, options, conf):
        self.conf = conf

    def _add_message(
            self, test, err=None, status=None):
        data = {
            'status': status,
            'time_taken': self.taken,
            'traceback': u'',
            'step': None,
            'message': u''
        }
        if err:
            exc_type, exc_value, exc_traceback = err
            if not status == 'error':
                data['step'], data['message'] = \
                    nose_utils.format_failure_message(exc_value)

        with self.session.begin(subtransactions=True):

            tests_to_update = nose_utils.get_tests_ids_to_update(test)

            for test_id in tests_to_update:
                models.Test.add_result(
                    self.session,
                    self.test_run_id,
                    test_id,
                    data
                )

    def addSuccess(self, test, capt=None):
        self._add_message(test, status='success')

    def addFailure(self, test, err):
        LOG.error('%s', test.id(), exc_info=err)
        self._add_message(test, err=err, status='failure')

    def addError(self, test, err):
        if err[0] is AssertionError:
            LOG.error('%s', test.id(), exc_info=err)
            self._add_message(test, err=err, status='failure')
        elif issubclass(err[0], unittest2.SkipTest):
            LOG.warning('%s is skipped', test.id())
            self._add_message(test, err=err, status='skipped')
        elif issubclass(err[0], InterruptTestRunException):
            raise
        else:
            LOG.error('%s', test.id(), exc_info=err)
            self._add_message(test, err=err, status='error')

    def beforeTest(self, test):
        self._start_time = time()
        self._add_message(test, status='running')

    def describeTest(self, test):
        return test.test._testMethodDoc

    @property
    def taken(self):
        if self._start_time:
            return time() - self._start_time
        return 0
