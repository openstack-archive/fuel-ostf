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

from distutils import version
import itertools
import logging
import multiprocessing
import os
import re
import traceback

from nose import case
from nose.suite import ContextSuite

from oslo.serialization import jsonutils

LOG = logging.getLogger(__name__)


def parse_json_file(file_path):
    current_directory = os.path.dirname(os.path.realpath(__file__))
    commands_path = os.path.join(
        current_directory, file_path)
    with open(commands_path, 'r') as f:
        return jsonutils.load(f)


def get_exc_message(exception_value):
    """Gets message from exception

    :param exception_value: Exception type object
    """
    _exc_long = str(exception_value)
    if isinstance(_exc_long, basestring):
        return _exc_long.split('\n')[0]
    return u""


def _process_docstring(docstring, pattern):
    pattern_matcher = re.search(pattern, docstring)

    if pattern_matcher:
        value = pattern_matcher.group(1)
        docstring = docstring[:pattern_matcher.start()]
    else:
        value = None

    return docstring, value


def get_description(test_obj):
    """Parses docstring of test object in order
    to get necessary data.

    test_obj.test._testMethodDoc is using directly
    instead of calling test_obj.shortDescription()
    for the sake of compability with python 2.6 where
    this method works pretty buggy.
    """
    if isinstance(test_obj, case.Test):
        docstring = test_obj.test._testMethodDoc

        test_data = {}
        if docstring:
            deployment_tags_pattern = r'Deployment tags:.?(?P<tags>.+)?'
            docstring, deployment_tags = _process_docstring(
                docstring,
                deployment_tags_pattern
            )

            # if deployment tags is empty or absent
            # _process_docstring returns None so we
            # must check this and prevent
            if deployment_tags:
                deployment_tags = [
                    tag.strip().lower() for tag in deployment_tags.split(',')
                ]

                test_data["deployment_tags"] = deployment_tags

            rel_vers_pattern = "Available since release:.?(?P<rel_vers>.+)"
            docstring, rel_vers = _process_docstring(
                docstring,
                rel_vers_pattern
            )
            if rel_vers:
                test_data["available_since_release"] = rel_vers

            duration_pattern = r'Duration:.?(?P<duration>.+)'
            docstring, duration = _process_docstring(
                docstring,
                duration_pattern
            )
            if duration:
                test_data["duration"] = duration

            docstring = docstring.split('\n')
            test_data["title"] = docstring.pop(0)
            test_data["description"] = \
                u'\n'.join(docstring) if docstring else u""

    return test_data


def modify_test_name_for_nose(test_path):
    test_module, test_class, test_method = test_path.rsplit('.', 2)
    return '{0}:{1}.{2}'.format(test_module, test_class, test_method)


def format_exception(exc_info):
    ec, ev, tb = exc_info

    # formatError() may have turned our exception object into a string, and
    # Python 3's traceback.format_exception() doesn't take kindly to that (it
    # expects an actual exception object).  So we work around it, by doing the
    # work ourselves if ev is a string.
    if isinstance(ev, basestring):
        tb_data = ''.join(traceback.format_tb(tb))
        return tb_data + ev
    else:
        return ''.join(traceback.format_exception(*exc_info))


def format_failure_message(message):
    message = get_exc_message(message)
    matcher = re.search(
        r'^[a-zA-Z]+\s?(\d+)\s?[a-zA-Z]+\s?[\.:]\s?(.+)',
        message)
    if matcher:
        step, msg = matcher.groups()
        return int(step), msg
    return None, message


def run_proc(func, *args):
    proc = multiprocessing.Process(
        target=func,
        args=args)
    proc.daemon = True
    proc.start()
    return proc


def get_module(module_path):
    pass


def get_tests_to_update(test):
    """Sometimes (e.g. unhandles exception is occured in
    setUpClass of test case) tests can be packed in
    separate ContextSuite each. At the moment of following code
    creation depth of this packaging was unknown so
    current function is implemented with recursion
    (which is not good by any means and you are free to
    modify that if you can)
    """
    tests = []

    if isinstance(test, case.Test):
        tests.append(test)
    elif isinstance(test, ContextSuite):
        for sub_test in test._tests:
            tests.extend(get_tests_to_update(sub_test))

    return tests


def _process_deployment_tags(cluster_depl_tags, test_depl_tags):
    """Process alternative deployment tags for testsets and tests
    and determines whether current test entity (testset or test)
    is appropriate for cluster.
    """

    test_depl_tags = [
        [alt_tag.strip() for alt_tag in tag.split('|')]
        for tag in test_depl_tags
    ]

    for comb in itertools.product(*test_depl_tags):
        if set(comb).issubset(cluster_depl_tags):
            return True

    return False


def _compare_release_versions(cluster_release_version, test_release_version):
    cl_openstack_ver, cl_fuel_ver = cluster_release_version.split('-')
    test_openstack_ver, test_fuel_ver = test_release_version.split('-')

    cond = (
        (version.StrictVersion(cl_openstack_ver) >=
         version.StrictVersion(test_openstack_ver))
        and
        (version.StrictVersion(cl_fuel_ver) >=
         version.StrictVersion(test_fuel_ver))
    )
    return cond


def tests_availability_cond(cluster_data, test_entity_data):
    is_test_available = False
    is_rel_ver_suitable = False

    # if 'available_since_release' attritube of test entity
    # is empty then this test entity is available for cluster
    # in other case execute release comparator logic
    if not test_entity_data['available_since_release']:
        is_rel_ver_suitable = True
    else:
        is_rel_ver_suitable = _compare_release_versions(
            cluster_data['release_version'],
            test_entity_data['available_since_release']
        )

    # if release version of test entity is suitable for cluster
    # then check test entity compatibility with cluster
    # by deployment tags
    if is_rel_ver_suitable:
        is_depl_tags_suitable = _process_deployment_tags(
            cluster_data['deployment_tags'],
            test_entity_data['deployment_tags']
        )
        if is_depl_tags_suitable:
            is_test_available = True

    return is_test_available
