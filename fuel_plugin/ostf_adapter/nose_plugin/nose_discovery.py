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
import pecan

from nose import plugins

from fuel_plugin.ostf_adapter.nose_plugin import nose_test_runner
from fuel_plugin.ostf_adapter.nose_plugin import nose_utils
from fuel_plugin.ostf_adapter.storage import engine, models


LOG = logging.getLogger(__name__)


class DiscoveryPlugin(plugins.Plugin):

    enabled = True
    name = 'discovery'
    score = 15000

    def __init__(self, deployment_info):
        self.test_sets = {}
        self.deployment_info = deployment_info
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

            if set(profile['deployment_tags']) \
               .issubset(self.deployment_info['deployment_tags']):

                profile['cluster_id'] = self.deployment_info['cluster_id']

                session = engine.get_session()
                with session.begin(subtransactions=True):
                    LOG.info('%s discovered.', module.__name__)
                    test_set = models.TestSet(**profile)
                    test_set = session.merge(test_set)
                    session.add(test_set)
                    self.test_sets[test_set.id] = test_set

    def addSuccess(self, test):
        test_id = test.id()
        for test_set_id in self.test_sets.keys():
            if test_set_id in test_id:
                session = engine.get_session()
                with session.begin(subtransactions=True):

                    data = dict()
                    data['cluster_id'] = self.deployment_info['cluster_id']
                    (data['title'], data['description'],
                     data['duration'], data['deployment_tags']) = \
                        nose_utils.get_description(test)
                    LOG.debug('%s - Cluster tags: %s', data,
                             self.deployment_info)
                    if set(data['deployment_tags'])\
                       .issubset(self.deployment_info['deployment_tags']):

                        data.update(
                            {
                                'test_set_id': test_set_id,
                                'name': test_id
                            }
                        )

                        #merge doesn't work here so we must check
                        #tests existing with such test_set_id and cluster_id
                        #so we won't ended up with dublicating data upon tests
                        #in db.
                        tests = session.query(models.Test)\
                            .filter_by(cluster_id=self.test_sets[test_set_id].cluster_id)\
                            .filter_by(test_set_id=test_set_id)\
                            .filter_by(test_run_id=None)\
                            .filter_by(name=data['name'])\
                            .first()

                        if not tests:
                            LOG.info('%s added for %s', test_id, test_set_id)
                            test_obj = models.Test(**data)
                            session.add(test_obj)


def discovery(path, deployment_info=None):
    """Will discover all tests on provided path and save info in db
    """
    deployment_info = deployment_info if deployment_info else dict()
    LOG.info('Starting discovery for %r.', path)

    nose_test_runner.SilentTestProgram(
        addplugins=[DiscoveryPlugin(deployment_info)],
        exit=False,
        argv=['tests_discovery', '--collect-only', path]
    )
