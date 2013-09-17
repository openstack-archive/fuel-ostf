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
from nose.suite import ContextSuite
from pecan import conf
from fuel_plugin.ostf_adapter.nose_plugin import nose_utils

from fuel_plugin.ostf_adapter.storage import models, engine


LOG = logging.getLogger(__name__)


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
            'time_taken': self.taken
        }
        data['title'], data['description'], data['duration'] = \
            nose_utils.get_description(test)
        if err:
            exc_type, exc_value, exc_traceback = err
            data['step'], data['message'] = None, u''
            if not status == 'error':
                data['step'], data['message'] = \
                    nose_utils.format_failure_message(exc_value)
            data['traceback'] = u''
        else:
            data['step'], data['message'] = None, u''
            data['traceback'] = u''

        session = engine.get_session()

        with session.begin(subtransactions=True):

            if isinstance(test, ContextSuite):
                for sub_test in test._tests:
                    data['title'], data['description'], data['duration'] = \
                        nose_utils.get_description(test)
                    models.Test.add_result(
                        session, self.test_run_id, sub_test.id(), data)
            else:
                models.Test.add_result(
                    session, self.test_run_id, test.id(), data)

    def addSuccess(self, test, capt=None):
        self._add_message(test, status='success')

    def addFailure(self, test, err):
        LOG.error('%s', test.id(), exc_info=err)
        self._add_message(test, err=err, status='failure')

    def addError(self, test, err):
        if err[0] == AssertionError:
            LOG.error('%s', test.id(), exc_info=err)
            self._add_message(
                test, err=err, status='failure')
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
