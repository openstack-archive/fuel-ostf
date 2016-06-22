import logging
import time

import neutronclient.neutron.client

LOG = logging.getLogger(__name__)

def wrap_neutron_client_call(func):
    """A function is any call to neutronclient instance.

    Wraps the func call in order to measure time that the method took
    to execute.
    """
    def wrapper(*args, **kwargs):
        LOG.info("Executing %s(%s, %s)" % (func.__name__, ",".join([str(a) for a in args]),
                                           ",".join("%s=%s" % (k, v) for k, v in kwargs.iteritems())))
        start = time.time()
        res = func(*args, **kwargs)
        LOG.info("Finished %s. Execution took %s" % (func.__name__, time.time() - start))
        return res

    return wrapper


class EnhancedNeutronClient(object):

    def __init__(self, version, token, endpoint_url, insecure=True):
        self.nc = neutronclient.neutron.client.Client(
	    version, token=token,
            endpoint_url=endpoint_url, insecure=insecure)

    def __getattr__(self, name):
        LOG.info("Preparing to call %s" % name)
        getattr_res = getattr(self.nc, name)
        if hasattr(getattr_res, '__call__'):
            getattr_res = wrap_neutron_client_call(getattr_res)
        return getattr_res
