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

from nose import plugins

from fuel_plugin.ostf_adapter.nose_plugin import nose_test_runner
from fuel_plugin.ostf_adapter.nose_plugin import nose_utils
from fuel_plugin.ostf_adapter.storage import engine, models


CORE_PATH = 'fuel_health'

LOG = logging.getLogger(__name__)


class DiscoveryPlugin(plugins.Plugin):

    enabled = True
    name = 'discovery'
    score = 15000

    def __init__(self):
        self.test_sets = {}
        super(DiscoveryPlugin, self).__init__()

    def options(self, parser, env=os.environ):
        pass

    def configure(self, options, conf):
        pass

    def afterImport(self, filename, module):
        module = __import__(module, fromlist=[module])
        LOG.info('Inspecting %s', filename)
        if hasattr(module, '__profile__'):
            session = engine.get_session()
            with session.begin(subtransactions=True):
                LOG.info('%s discovered.', module.__name__)
                test_set = models.TestSet(**module.__profile__)
                test_set = session.merge(test_set)
                session.add(test_set)
                self.test_sets[test_set.id] = test_set

    def addSuccess(self, test):
        test_id = test.id()
        for test_set_id in self.test_sets.keys():
            if test_set_id in test_id:
                session = engine.get_session()
                with session.begin(subtransactions=True):
                    LOG.info('%s added for %s', test_id, test_set_id)
                    data = dict()
                    data['title'], data['description'], data['duration'] = \
                        nose_utils.get_description(test)
                    old_test_obj = session.query(models.Test).filter_by(
                        name=test_id, test_set_id=test_set_id,
                        test_run_id=None).\
                        update(data, synchronize_session=False)
                    if not old_test_obj:
                        data.update({'test_set_id': test_set_id,
                                     'name': test_id})
                        test_obj = models.Test(**data)
                        session.add(test_obj)


def discovery(path=None):
    """
        function to automaticly discover any test packages
    """

    tests = [CORE_PATH, path] if path else [CORE_PATH]
    LOG.info('Starting discovery for %r.', tests)
    nose_test_runner.SilentTestProgram(
        addplugins=[DiscoveryPlugin()],
        exit=False,
        argv=['tests_discovery', '--collect-only'] + tests)
