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

from functools import wraps
from unittest import TestCase

from fuel_plugin.ostf_client.client import TestingAdapterClient


class EmptyResponseError(Exception):
    pass


class Response(object):
    """This is testing_adapter response object"""
    test_name_mapping = {}

    def __init__(self, response):
        self.is_empty = False
        if isinstance(response, list):
            self._parse_json(response)
            self.request = None
        else:
            self._parse_json(response.json())
            self.request = '{0} {1} \n with {2}'\
                .format(response.request.method, response.request.url, response.request.body)

    def __getattr__(self, item):
        if item in self.test_sets or item in self._tests:
            return self.test_sets.get(item) or self._tests.get(item)
        else:
            return super(type(self), self).__delattr__(item)

    def __str__(self):
        if self.is_empty:
            return "Empty"
        return self.test_sets.__str__()

    @classmethod
    def set_test_name_mapping(cls, mapping):
        cls.test_name_mapping = mapping

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
            self._tests = dict((self._friendly_name(item.get('id')), item) for item in testset['tests'])

    def _friendly_name(self, name):
        return self.test_name_mapping.get(name, name)


class AdapterClientProxy(object):

    def __init__(self, url):
        self.client = TestingAdapterClient(url)

    def __getattr__(self, item):
        if item in TestingAdapterClient.__dict__:
            call = getattr(self.client, item)
            return self._decorate_call(call)
    def _friendly_map(self, mapping):
        Response.set_test_name_mapping(mapping)

    def _decorate_call(self, call):
        @wraps(call)
        def inner(*args, **kwargs):
            r = call(*args, **kwargs)
            return Response(r)
        return inner




class SubsetException(Exception):
    pass


class BaseAdapterTest(TestCase):
    def compare(self, response, comparable):
        if response.is_empty:
            msg = '{0} is empty'.format(response.request)
            raise AssertionError(msg)
        if not isinstance(comparable, Response):
            comparable = Response(comparable)
        test_set = comparable.test_sets.keys()[0]
        test_set_data = comparable.test_sets[test_set]
        tests = comparable._tests
        diff = []

        for item in test_set_data:
            if item == 'tests':
                continue
            if response.test_sets[test_set][item] != test_set_data[item]:
                msg = 'Actual "{0}" !=  expected "{1}" in {2}.{3}'.format(response.test_sets[test_set][item],
                                                                          test_set_data[item], test_set, item)
                diff.append(msg)

        for test_name, test in tests.iteritems():
            for t in test:
                if t == 'id':
                    continue
                if response._tests[test_name][t] != test[t]:
                    msg = 'Actual "{0}" !=  expected"{1}" in {2}.{3}.{4}'.format(response._tests[test_name][t],
                                                                                 test[t], test_set, test_name, t)
                    diff.append(msg)
        if diff:
            raise AssertionError(diff)

    @staticmethod
    def init_client(url, mapping):
        ac = AdapterClientProxy(url)
        ac._friendly_map(mapping)
        return ac


