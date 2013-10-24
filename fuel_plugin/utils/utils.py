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

from sqlalchemy.orm import joinedload

from fuel_plugin.ostf_adapter.storage import engine, models, simple_cache


def clean_db():
    eng = engine.get_engine()

    conn = eng.connect()

    conn.execute('delete from cluster_testing_pattern;')
    conn.execute('delete from cluster_state;')
    conn.execute('delete from test_sets;')

    conn.close()


def cache_data():
    session = engine.get_session()

    with session.begin(subtransactions=True):
        test_repository = session.query(models.TestSet)\
            .options(joinedload('tests'))\
            .all()

        crucial_tests_attrs = ['name', 'deployment_tags']
        for test_set in test_repository:
            data_elem = dict()

            data_elem['test_set_id'] = test_set.id
            data_elem['deployment_tags'] = test_set.deployment_tags
            data_elem['tests'] = []

            for test in test_set.tests:
                test_dict = dict([(attr_name, getattr(test, attr_name))
                                  for attr_name in crucial_tests_attrs])
                data_elem['tests'].append(test_dict)

            simple_cache.TEST_REPOSITORY.append(data_elem)
