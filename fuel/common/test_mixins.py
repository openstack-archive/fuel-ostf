# Copyright 2013 Mirantis, Inc.
# All Rights Reserved.


class FuelTestAssertMixin(object):
    """
    Mixin class with a set of assert methods created to abstract
    from unittest assertion methods and provide human
    readable descriptions where it is possible
    """
    def verify_response_status(self, status, appl='Application', msg=None):
        """

        Method provides human readable message
        for the HTTP response status verification

        :param appl: the name of application requested
        :param status: response status
        :param msg: message to be used instead the default one
        """
        if status == 200:
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

        msg = '{appl} status - {status} is unknown'

        if status in human_readable_statuses:
            status_msg = human_readable_statuses[status].format(
                status=status, application=appl)
        else:
            status_msg = human_readable_status_groups.get(status / 100, msg).\
                format(status=status, application=appl)

        self.assertEquals(200,
                          status,
                          ''.join(('Status - {status}'.format(status=status),
                                   status_msg, '\n', msg)))

    def verify_response_body(self, body, content):
        """

        Method provides human readable message for the verification if
        HTTP response body contains desired keyword

        :param body: response body
        :param content: content that should be present in the response body
        """
        if content in body:
            return

        self.asserTrue(content in body)
