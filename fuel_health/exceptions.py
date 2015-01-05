# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

import unittest2


class FuelException(Exception):
    """Base Exception

    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printf'd
    with the keyword arguments provided to the constructor.
    """
    message = "An unknown exception occurred"

    def __init__(self, *args, **kwargs):
        super(FuelException, self).__init__()
        try:
            self._error_string = self.message % kwargs
        except Exception:
            # at least get the core message out if something happened
            self._error_string = self.message
        if len(args) > 0:
            # If there is a non-kwarg parameter, assume it's the error
            # message or reason description and tack it on to the end
            # of the exception message
            # Convert all arguments into their string representations...
            args = ["%s" % arg for arg in args]
            self._error_string = (self._error_string +
                                  "\nDetails: %s" % '\n'.join(args))

    def __str__(self):
        return self._error_string


class InvalidConfiguration(FuelException):
    message = "Invalid Configuration"


class SetProxy(InvalidConfiguration):
    message = ("Can not set proxy for Health Check."
               "Make sure that network configuration on controllers are fine")


class OfflineControllers(InvalidConfiguration):
    message = ('Can not check health of cluster.'
               ' All controllers are offline')


class RestClientException(FuelException,
                          unittest2.TestCase.failureException):
    pass


class NotFound(RestClientException):
    message = "Object not found"


class Unauthorized(RestClientException):
    message = 'Unauthorized'


class TimeoutException(FuelException):
    message = "Request timed out"


class BuildErrorException(FuelException):
    message = "Server %(server_id)s failed to build and is in ERROR status"


class AddImageException(FuelException):
    message = "Image %(image_id)s failed to become ACTIVE in the allotted time"


class EC2RegisterImageException(FuelException):
    message = ("Image %(image_id)s failed to become 'available' "
               "in the allotted time")


class VolumeBuildErrorException(FuelException):
    message = "Volume %(volume_id)s failed to build and is in ERROR status"


class SnapshotBuildErrorException(FuelException):
    message = "Snapshot %(snapshot_id)s failed to build and is in ERROR status"


class StackBuildErrorException(FuelException):
    message = ("Stack %(stack_identifier)s is in %(stack_status)s status "
               "due to '%(stack_status_reason)s'")


class BadRequest(RestClientException):
    message = "Bad request"


class UnprocessableEntity(RestClientException):
    message = "Unprocessable entity"


class AuthenticationFailure(RestClientException):
    message = ("Authentication with user %(user)s and password "
               "%(password)s failed")


class EndpointNotFound(FuelException):
    message = "Endpoint not found"


class RateLimitExceeded(FuelException):
    message = ("Rate limit exceeded.\nMessage: %(message)s\n"
               "Details: %(details)s")


class OverLimit(FuelException):
    message = "Quota exceeded"


class ComputeFault(FuelException):
    message = "Got compute fault"


class ImageFault(FuelException):
    message = "Image for tests not found"


class IdentityError(FuelException):
    message = "Got identity error"


class Duplicate(RestClientException):
    message = "An object with that identifier already exists"


class SSHTimeout(FuelException):
    message = ("Connection to the %(host)s via SSH timed out.\n"
               "User: %(user)s, Password: %(password)s")


class SSHExecCommandFailed(FuelException):
    """Raised when remotely executed command returns nonzero status."""
    message = ("Command '%(command)s', exit status: %(exit_status)d, "
               "Error:\n%(strerror)s")


class ServerUnreachable(FuelException):
    message = "The server is not reachable via the configured network"


class SQLException(FuelException):
    message = "SQL error: %(message)s"


class TearDownException(FuelException):
    message = "%(num)d cleanUp operation failed"


class RFCViolation(RestClientException):
    message = "RFC Violation"


class ResponseWithNonEmptyBody(RFCViolation):
    message = ("RFC Violation! Response with %(status)d HTTP Status Code "
               "MUST NOT have a body")


class ResponseWithEntity(RFCViolation):
    message = ("RFC Violation! Response with 205 HTTP Status Code "
               "MUST NOT have an entity")
