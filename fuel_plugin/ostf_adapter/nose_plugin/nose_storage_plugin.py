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

import logging
import os
import time

from nose import plugins
from oslo_config import cfg

from fuel_plugin.ostf_adapter.nose_plugin import nose_utils
from fuel_plugin.ostf_adapter.storage import models

CONF = cfg.CONF


LOG = logging.getLogger(__name__)


class StoragePlugin(plugins.Plugin):
    enabled = True
    name = 'storage'
    score = 15000

    def __init__(self, session, test_run_id, cluster_id,
                 ostf_os_access_creds, token, results_log):

        self.session = session
        self.test_run_id = test_run_id
        self.cluster_id = cluster_id
        self.ostf_os_access_creds = ostf_os_access_creds
        self.results_log = results_log

        super(StoragePlugin, self).__init__()
        self._start_time = None
        self.token = token

    def options(self, parser, env=os.environ):
        env['NAILGUN_HOST'] = str(CONF.adapter.nailgun_host)
        env['NAILGUN_PORT'] = str(CONF.adapter.nailgun_port)
        if self.token is not None:
            env['NAILGUN_TOKEN'] = self.token
        if self.cluster_id:
            env['CLUSTER_ID'] = str(self.cluster_id)

        for var_name in self.ostf_os_access_creds:
            env[var_name.upper()] = self.ostf_os_access_creds[var_name]

    def configure(self, options, conf):
        self.conf = conf

    def _add_test_results(self, test, data):
        test_id = test.id()

        models.Test.add_result(
            self.session,
            self.test_run_id,
            test_id,
            data
        )
        if data['status'] != 'running':
            test_name = nose_utils.get_description(test)["title"]
            self.results_log.log_results(
                test_id,
                test_name=test_name,
                status=data['status'],
                message=data['message'],
                traceback=data['traceback'],
            )

    def _add_message(self, test, err=None, status=None):
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

            if status != 'skipped':
                data['traceback'] = nose_utils.format_exception(err)

        tests_to_update = nose_utils.get_tests_to_update(test)

        for test in tests_to_update:
            self._add_test_results(test, data)
        self.session.commit()

    def addSuccess(self, test, capt=None):
        self._add_message(test, status='success')

    def addFailure(self, test, err):
        LOG.error('%s', test.id(), exc_info=err)
        self._add_message(test, err=err, status='failure')

    def addError(self, test, err):
        if err[0] is AssertionError:
            LOG.error('%s', test.id(), exc_info=err)
            self._add_message(test, err=err, status='failure')
        elif issubclass(err[0], plugins.skip.SkipTest):
            LOG.warning('%s is skipped', test.id())
            self._add_message(test, err=err, status='skipped')
        else:
            LOG.error('%s', test.id(), exc_info=err)
            self._add_message(test, err=err, status='error')

    def beforeTest(self, test):
        self._start_time = time.time()
        self._add_message(test, status='running')

    def describeTest(self, test):
        return test.test._testMethodDoc

    @property
    def taken(self):
        if self._start_time:
            return time.time() - self._start_time
        return 0
