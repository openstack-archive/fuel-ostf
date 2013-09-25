# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import signal
import time

from fuel_health.common import log as logging

LOG = logging.getLogger(__name__)


class FuelTestAssertMixin(object):
    """
    Mixin class with a set of assert methods created to abstract
    from unittest assertion methods and provide human
    readable descriptions where possible
    """
    def verify_response_status(self, status,
                               appl='Application', msg='', failed_step=''):
        """

        Method provides human readable message
        for the HTTP response status verification

        :param appl: the name of application requested
        :param status: response status
        :param msg: message to be used instead the default one
        :failed_step: the step of the test scenario that has failed
        """
        if status in [200, 201, 202]:
            return

        human_readable_statuses = {
            400: ('Something changed in {appl} and request is no '
                  'longer recognized as valid. Please verify that you '
                  'are not sending an HTTP request to an HTTPS socket'),
            401: 'Unauthorized, please check Keystone and {appl} connectivity',
            403: ('Forbidden, please check if Keystone and {appl} '
                  'security policies have changed'),
            404: '{appl} server is running but the application is not found',
            500: '{appl} server is experiencing some problems',
            503: '{appl} server is experiencing problems'
        }

        human_readable_status_groups = {
            3: ('Status {status}. Redirection. Please check that all {appl}'
                ' proxy settings are correct'),
            4: ('Status {status}. Client error. Please verify that your {appl}'
                ' configuration corresponds to the one defined in '
                'Fuel configuration '),
            5: 'Status {status}. Server error. Please check {appl} logs'
        }

        unknown_msg = '{appl} status - {status} is unknown'

        if status in human_readable_statuses:
            status_msg = human_readable_statuses[status].format(
                status=status, appl=appl)
        else:
            status_msg = human_readable_status_groups.get(
                status / 100, unknown_msg).format(status=status, appl=appl)

        failed_step_msg = ''
        if failed_step:
            failed_step_msg = ('Step %s failed: ' % str(failed_step))

        self.fail(''.join((failed_step_msg +
                           'Status - {status} '.format(
                               status=status), status_msg, '\n', msg)))

    def verify_response_body(self, body, content='', msg='', failed_step=''):
        """
        Method provides human readable message for the verification if
        HTTP response body contains desired keyword

        :param body: response body
        :param content: content type that should be present in response body
        :param msg: message to be used instead the default one
        """
        if content in body:
            return
        if failed_step:
            msg = ('Step %s failed: ' % str(failed_step)) + msg
        self.fail(msg)

    def verify_response_body_value(self, body_structure, value='', msg='',
                                   failed_step=''):
        """
        Method provides human readable message for verification if
        HTTP response body element contains desired keyword.

        :param body_structure: body element value (e.g. body['name'], body);
        :param value: expected value of body element (e.g. u'test-flavor');
        :param msg: message to be used instead of the default one.
        """
        if type(body_structure) is dict:
            if value in body_structure.values():
                return
        else:
            if body_structure == value:
                return
        failed_step_msg = ''
        if failed_step:
            failed_step_msg = ('Step {step} failed: {msg}{refer}'.format(
                step=str(failed_step),
                msg=msg,
                refer=" Please refer to OpenStack"
                      " logs for more details."))
        self.fail(failed_step_msg)

    def verify_response_body_content(self, exp_content, act_content, msg='',
                                     failed_step=''):
        if exp_content == act_content:
            return
        if failed_step:
            failed_step_msg = ('Step %s failed: ' % str(failed_step))
        self.fail(''.join(failed_step_msg +
                          'Actual value - {actual_content}'.format(
                              actual_content=act_content), '\n', msg))

    def verify_response_body_not_equal(self, exp_content, act_content, msg='',
                                       failed_step=''):
        if exp_content != act_content:
            return
        if failed_step:
            failed_step_msg = ('Step %s failed: ' % str(failed_step))
        self.fail(''.join((failed_step_msg +
                           'Actual value - {actual_content}'.format(
                               actual_content=act_content), '\n', msg)))

    def verify_response_true(self, resp, msg):
        if resp:
            return
        self.fail(msg + " Please refer to OpenStack logs for more details.")

    def verify(self, secs, func, step='', msg='', action='', *args, **kwargs):
        """
        Arguments:
        :secs: timeout time;
        :func: function to be verified;
        :step: number of test step;
        :msg: message that will be displayed if an exception occurs;
        :action: action that is performed by the method.
        """
        try:
            with timeout(secs, action):
                result = func(*args, **kwargs)
        except Exception as exc:
            LOG.debug(exc)
            if type(exc) is AssertionError:
                msg = str(exc)
            self.fail("Step %s failed: " % step + msg +
                      " Please refer to OpenStack logs for more details.")
        else:
            return result


class TimeOutError(Exception):
    def __init__(self):
        Exception.__init__(self)


def _raise_TimeOut(sig, stack):
    raise TimeOutError()


class timeout(object):
    """
    Timeout context that will stop code running within context
    if timeout is reached

    >>with timeout(2):
    ...     requests.get("http://msdn.com")
    """
    def __init__(self, timeout, action):
        self.timeout = timeout
        self.action = action

    def __enter__(self):
        signal.signal(signal.SIGALRM, _raise_TimeOut)
        signal.alarm(self.timeout)

    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)  # disable the alarm
        if exc_type is not TimeOutError:
            return False  # never swallow other exceptions
        else:
            msg = ("Time limit exceeded while waiting for {call} to "
                   "finish.").format(call=self.action)
            raise AssertionError(msg)
