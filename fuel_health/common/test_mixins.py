# Copyright 2013 Mirantis, Inc.
# All Rights Reserved.


class FuelTestAssertMixin(object):
    """
    Mixin class with a set of assert methods created to abstract
    from unittest assertion methods and provide human
    readable descriptions where it is possible
    """
    def verify_response_status(self, status, appl='Application', msg='', failed_step=''):
        """

        Method provides human readable message
        for the HTTP response status verification

        :param appl: the name of application requested
        :param status: response status
        :param msg: message to be used instead the default one
        :failed_step: specifies step of the test scenario was not successful
        """
        if status in [200, 201, 202]:
            return

        human_readable_statuses = {
            400: ('Something changed in {appl} and request is no '
                  'longer recognized as valid. Please verify that you '
                  'are not trying to address HTTP request to HTTPS socket'),
            401: 'Unauthorized, please check Keystone and {appl} connectivity',
            403: ('Forbidden, please verify Keystone and {appl} '
                  'security policies did not change'),
            404: '{appl} server is running but application is not found',
            500: '{appl} server is experiencing some problems',
            503: '{appl} server is experiencing problems'
        }

        human_readable_status_groups = {
            3: ('Status {status}. Redirection. Please check that all {appl}'
                ' proxy settings are set correctly'),
            4: ('Status {status}. Client error. Please verify that your {appl}'
                ' configurations corresponds to re one defined in '
                'Fuel configuration '),
            5: 'Status {status}. Server error. Please check {appl} logs'
        }

        unknown_msg = '{appl} status - {status} is unknown'

        if status in human_readable_statuses:
            status_msg = human_readable_statuses[status].format(
                status=status, appl=appl)
        else:
            status_msg = human_readable_status_groups.get(status / 100,
                unknown_msg).format(status=status, appl=appl)

        failed_step_msg = ''
        if failed_step:
            failed_step_msg = ('Step %s failed: ' % str(failed_step))

        self.fail(''.join((failed_step_msg +
                           'Status - {status} '.format(status=status),
                            status_msg, '\n', msg)))

    def verify_response_body(self, body, content='', msg='', failed_step=''):
        """
        Method provides human readable message for the verification if
        HTTP response body contains desired keyword

        :param body: response body
        :param content: content type that should be present in the response body
        :param msg: message to be used instead the default one
        """
        if content in body:
            return
        if failed_step:
            msg = ('Step %s failed: ' % str(failed_step)) + msg
        self.fail(msg)

    def verify_response_body_value(self, body_structure, value='', msg='', failed_step=''):
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
            failed_step_msg = ('Step %s failed: ' % str(failed_step))
        self.fail(failed_step_msg + body_structure + '!=' + value + ' ' + msg)

    def verify_response_body_content(self, exp_content, act_content, msg='', failed_step=''):
        if exp_content == act_content:
            return
        if failed_step:
            failed_step_msg = ('Step %s failed. ' % str(failed_step))
        self.fail(''.join(failed_step_msg +
                          'Actual value - {actual_content}'.format(
                              actual_content=act_content), '\n', msg))
