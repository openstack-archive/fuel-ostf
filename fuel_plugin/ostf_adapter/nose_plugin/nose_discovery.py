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

import logging
import os

from nose import plugins

from fuel_plugin.ostf_adapter.nose_plugin import nose_test_runner
from fuel_plugin.ostf_adapter.nose_plugin import nose_utils
from fuel_plugin.ostf_adapter.storage import models


LOG = logging.getLogger(__name__)


class DiscoveryPlugin(plugins.Plugin):

    enabled = True
    name = 'discovery'
    score = 15000

    def __init__(self, session):
        self.session = session
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
            profile = module.__profile__

            profile['deployment_tags'] = [
                tag.lower() for tag in profile.get('deployment_tags', [])
            ]

            try:
                test_set = models.TestSet(**profile)
                self.session.merge(test_set)
                self.test_sets[test_set.id] = test_set

                #flush test_sets data into db
                self.session.commit()
            except Exception as e:
                LOG.error(
                    ('An error has occured while processing'
                     ' data entity for %s. Error message: %s'),
                    module.__name__,
                    e.message
                )
            LOG.info('%s discovered.', module.__name__)

    def addSuccess(self, test):
        test_id = test.id()
        for test_set_id in self.test_sets.keys():
            if test_set_id in test_id:
                data = dict()

                (data['title'], data['description'],
                 data['duration'], data['deployment_tags']) = \
                    nose_utils.get_description(test)

                data.update(
                    {
                        'test_set_id': test_set_id,
                        'name': test_id
                    }
                )

                try:
                    test_obj = models.Test(**data)
                    self.session.merge(test_obj)

                    #flush tests data into db
                    self.session.commit()
                except Exception as e:
                    LOG.error(
                        ('An error has occured while '
                         'processing data entity for '
                         'test with name %s. Error message: %s'),
                        test_id,
                        e.message
                    )
                LOG.info('%s added for %s', test_id, test_set_id)


def discovery(path, session):
    """Will discover all tests on provided path and save info in db
    """
    LOG.info('Starting discovery for %r.', path)

    nose_test_runner.SilentTestProgram(
        addplugins=[DiscoveryPlugin(session)],
        exit=False,
        argv=['tests_discovery', '--collect-only', '--nocapture', path]
    )
