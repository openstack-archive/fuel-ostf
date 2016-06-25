# Copyright 2016 Mirantis, Inc.
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


import logging
import time

LOG = logging.getLogger(__name__)

try:
    import neutronclient.neutron.client
except Exception:
    LOG.exception()
    LOG.warning('Neutron client could not be imported.')


def wrap_neutron_client_call(func):
    """A function is a call to neutronclient instance.

    Wraps the func call in order to measure time that the method took
    to execute.
    """
    def wrapper(*args, **kwargs):
        LOG.info("Executing %s(%s %s)" %
                 (func.__name__, ",".join([str(a) for a in args]),
                  ",".join("%s=%s" % (k, v) for k, v in kwargs.iteritems())))
        start = time.time()
        res = func(*args, **kwargs)
        LOG.info("Finished %s. Execution took %s" %
                 (func.__name__, time.time() - start))
        return res

    return wrapper


class EnhancedNeutronClient(object):

    def __init__(self, version, token, endpoint_url, insecure=True):
        self.nc = neutronclient.neutron.client.Client(
            version, token=token, endpoint_url=endpoint_url, insecure=insecure)

    def __getattr__(self, name):
        getattr_res = getattr(self.nc, name)
        if hasattr(getattr_res, '__call__'):
            getattr_res.__name__ = name
            getattr_res = wrap_neutron_client_call(getattr_res)
        return getattr_res
