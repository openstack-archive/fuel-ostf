# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
# Copyright 2013 Mirantis, Inc.
# All Rights Reserved.
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

import time
import traceback

import testresources
import unittest2

from fuel_health.common import log as logging
from fuel_health.common.ssh import Client as SSHClient
from fuel_health.common.test_mixins import FuelTestAssertMixin
from fuel_health import config


LOG = logging.getLogger(__name__)


class BaseTestCase(unittest2.TestCase,
                   testresources.ResourcedTestCase,
                   FuelTestAssertMixin):

    def __init__(self, *args, **kwargs):
        super(BaseTestCase, self).__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        if hasattr(super(BaseTestCase, cls), 'setUpClass'):
            super(BaseTestCase, cls).setUpClass()
        cls.config = config.FuelConfig()


def call_until_true(func, duration, sleep_for, *args):
    """Call the given function until it returns True (and return True) or
    until the specified duration (in seconds) elapses (and return
    False).

    :param func: A zero argument callable that returns True on success.
    :param duration: The number of seconds for which to attempt a
        successful call of the function.
    :param sleep_for: The number of seconds to sleep after an unsuccessful
                      invocation of the function.
    """
    now = time.time()
    timeout = now + duration
    while now < timeout:
        if args:
            if func(*args):
                return True
        elif func():
            return True
        LOG.debug("Sleeping for %d seconds", sleep_for)
        time.sleep(sleep_for)
        now = time.time()
    return False


class TestCase(BaseTestCase):
    """Base test case class for all tests

    Contains basic setup and convenience methods
    """

    manager_class = None

    @classmethod
    def setUpClass(cls):
        super(TestCase, cls).setUpClass()
        cls.manager = cls.manager_class()
        for attr_name in cls.manager.client_attr_names:
            # Ensure that pre-existing class attributes won't be
            # accidentally overridden.
            assert not hasattr(cls, attr_name)
            client = getattr(cls.manager, attr_name)
            setattr(cls, attr_name, client)
        cls.resource_keys = {}
        cls.os_resources = []

    def set_resource(self, key, thing):
        LOG.debug("Adding %r to shared resources of %s" %
                  (thing, self.__class__.__name__))
        self.resource_keys[key] = thing
        self.os_resources.append(thing)

    def get_resource(self, key):
        return self.resource_keys[key]

    def remove_resource(self, key):
        thing = self.resource_keys[key]
        self.os_resources.remove(thing)
        del self.resource_keys[key]

    def status_timeout(self, things, thing_id, expected_status):
        """Given a thing and an expected status, do a loop, sleeping
        for a configurable amount of time, checking for the
        expected status to show. At any time, if the returned
        status of the thing is ERROR, fail out.
        """
        def check_status():
            # python-novaclient has resources available to its client
            # that all implement a get() method taking an identifier
            # for the singular resource to retrieve.
            thing = things.get(thing_id)
            new_status = thing.status.lower()
            if new_status == 'error':
                self.fail("Failed to get to expected status. "
                          "In error state.")
            elif new_status == expected_status.lower():
                return True  # All good.
            LOG.debug("Waiting for %s to get to %s status. "
                      "Currently in %s status",
                      thing, expected_status, new_status)
        conf = config.FuelConfig()
        if not call_until_true(check_status,
                               conf.compute.build_timeout,
                               conf.compute.build_interval):
            self.fail("Timed out waiting to become %s"
                      % expected_status)

    def run_ssh_cmd_with_exit_code(self, host, cmd):
        """Open SSH session with host and execute command.

        Fail if exit code != 0
        """
        try:
            sshclient = SSHClient(host, self.usr, self.pwd,
                                  key_filename=self.key, timeout=self.timeout)
            return sshclient.exec_command(cmd)
        except Exception:
            LOG.debug(traceback.format_exc())
            self.fail("{0} command failed.".format(cmd))
