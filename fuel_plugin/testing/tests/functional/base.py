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

import functools
import unittest

from fuel_plugin.ostf_client.client import TestingAdapterClient


class EmptyResponseError(Exception):
    pass


class Response(object):
    """This is testing_adapter response object."""
    test_name_mapping = {}

    def __init__(self, response):
        self.is_empty = False
        if isinstance(response, list):
            self._parse_json(response)
            self.request = None
        else:
            self._parse_json(response.json())
            self.request = '{0} {1} \n with {2}'\
                .format(
                    response.request.method,
                    response.request.url,
                    response.request.body
                )

    def __getattr__(self, item):
        if item in self.test_sets:
            return self.test_sets.get(item)

    def __str__(self):
        if self.is_empty:
            return "Empty"
        return self.test_sets.__str__()

    def _parse_json(self, json):
        if json == [{}]:
            self.is_empty = True
            return
        else:
            self.is_empty = False

        self.test_sets = {}
        self._tests = {}

        for testset in json:
            self.test_sets[testset.pop('testset')] = testset


class AdapterClientProxy(object):

    def __init__(self, url):
        self.client = TestingAdapterClient(url)

    def __getattr__(self, item):
        if item in TestingAdapterClient.__dict__:
            call = getattr(self.client, item)
            return self._decorate_call(call)

    def _decorate_call(self, call):
        @functools.wraps(call)
        def inner(*args, **kwargs):
            r = call(*args, **kwargs)
            return Response(r)
        return inner


class SubsetException(Exception):
    pass


class BaseAdapterTest(unittest.TestCase):
    def compare(self, response, comparable):
        if response.is_empty:
            msg = '{0} is empty'.format(response.request)
            raise AssertionError(msg)
        if not isinstance(comparable, Response):
            comparable = Response(comparable)

        for test_set in comparable.test_sets.keys():
            test_set_data = comparable.test_sets[test_set]
            tests = test_set_data['tests']
            diff = []

            for item in test_set_data:
                if item == 'tests':
                    continue
                if response.test_sets[test_set][item] != test_set_data[item]:
                    msg = 'Actual "{0}" !=  expected "{1}" in {2}.{3}'.format(
                        response.test_sets[test_set][item],
                        test_set_data[item],
                        test_set,
                        item
                    )
                    diff.append(msg)
                    raise AssertionError(msg)

            tests = dict([(test['id'], test) for test in tests])
            response_tests = dict(
                [
                    (test['id'], test) for test in
                    response.test_sets[test_set]['tests']
                ]
            )

            for test_id, test_data in tests.items():
                for data_key, data_value in test_data.items():
                    if not response_tests[test_id][data_key] == data_value:
                        msg = ('Actual "{4}" != expected data value '
                               '"{3}" with key "{2}" for test with id'
                               ' "{1}" of testset "{0}"')
                        msg = msg.format(
                            test_set,
                            test_id,
                            data_key,
                            data_value,
                            response_tests[test_id][data_key]
                        )
                        raise AssertionError(msg)

    @staticmethod
    def init_client(url):
        ac = AdapterClientProxy(url)
        return ac
