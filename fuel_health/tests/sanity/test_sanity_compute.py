from nose.plugins.attrib import attr
from nose.tools import timed

from fuel_health.tests.sanity import base

class SanityComputeTest(base.BaseComputeTest):
    """
    TestClass contains tests check base Compute functionality.
    """
    _interface = 'json'

    @attr(type=['sanity', 'fuel'])
    @timed(5.5)
    def test_list_instances(self):
        """Instances list availability
        Test checks list of instances is available.
        Target component: Nova
        Scenario:
            1. Request list of instances.
            2. Check response status is equal to 200.
            3. Check response contains "servers" section.
        Duration: 1-6 s.
        """
        fail_msg = 'Servers list is unavailable. ' \
                       'Looks like something is broken in Nova.'
        try:
            resp, body = self.servers_client.list_servers()
        except Exception as exc:
            base.error(exc)
            self.fail("Step 1 failed: " + fail_msg)

        self.verify_response_status(resp.status, u'Nova', fail_msg, 2)
        self.verify_response_body(body, u'servers', fail_msg, 3)

    @attr(type=['sanity', 'fuel'])
    @timed(7.5)
    def test_list_images(self):
        """Images list availability
        Test checks list of images is available.
        Target component: Glance
        Scenario:
            1. Request list of images.
            2. Check response status is equal to 200.
            3. Check response contains "images" section.
        Duration: 1-6 s.
        """
        fail_msg = 'Images list is unavailable. ' \
                   'Looks like something is broken in Glance.'
        try:
            resp, body = self.images_client.list_images()
        except Exception as exc:
            base.error(exc)
            self.fail("Step 1 failed: " + fail_msg)
        self.verify_response_status(resp.status, 'Glance')
        self.verify_response_body(body, u'images', fail_msg, 3)

    @attr(type=['sanity', 'fuel'])
    @timed(5.5)
    def test_list_volumes(self):
        """Volumes list availability
        Test checks list of volumes is available.
        Target component: Swift

        Scenario:
            1. Request list of volumes.
            2. Check response status is equal to 200.
            3. Check response contains "volumes" section.
        Duration: 1-6 s.
        """
        fail_msg = 'Volumes list is unavailable. ' \
                   'Looks like something is broken in Swift.'
        try:
            resp, body = self.volumes_client.list_volumes()
        except Exception as exc:
            base.error(exc)
            self.fail("Step 1 failed: " + fail_msg)
        self.verify_response_status(resp.status, 'Swift', fail_msg, 2)
        self.verify_response_body(body, u'volumes', fail_msg, 3)

    @attr(type=['sanity', 'fuel'])
    @timed(5.5)
    def test_list_snapshots(self):
        """Snapshots list availability
        Test checks list of snapshots is available.
        Target component: Swift

        Scenario:
            1. Request list of snapshots.
            2. Check response status is equal to 200.
            3. Check response contains "snapshots" section.
        Duration: 1-6 s.
        """
        fail_msg = 'Snapshots list is unavailable. ' \
                   'Looks like something is broken in Swift.'
        try:
            resp, body = self.snapshots_client.list_snapshots()
        except Exception as exc:
            base.error(exc)
            self.fail("Step 1 failed: " + fail_msg)
        self.verify_response_status(resp.status, 'Swift', fail_msg, 2)
        self.verify_response_body(body, u'snapshots', fail_msg, 3)

    @attr(type=['sanity', 'fuel'])
    @timed(5.5)
    def test_list_flavors(self):
        """Flavors list availability
        Test checks list of flavors is available.
        Target component: Nova

        Scenario:
            1. Request list of flavors.
            2. Check response status is equal to 200.
            3. Check response contains "flavors" section.
        Duration: 2-6 s.
        """
        fail_msg = 'Flavors list is unavailable. ' \
                   'Looks like something is broken in Nova.'
        try:
            resp, body = self.flavors_client.list_flavors()
        except Exception as exc:
            base.error(exc)
            self.fail("Step 1 failed: " + fail_msg)
        self.verify_response_status(resp.status, 'Nova', fail_msg, 2)
        self.verify_response_body(body, u'flavors', fail_msg, 3)

    @attr(type=['sanity', 'fuel'])
    @timed(5.5)
    def test_list_rate_limits(self):
        """Limits list availability
        Test checks list of absolute limits is available.
        Target component: Cinder

        Scenario:
            1. Request list of limits.
            2. Check response status is equal to 200.
            3. Check response contains absolute limits in "limits" section.
        Duration: 2-6 s.
        """
        fail_msg = 'Limits are unavailable. ' \
                   'Looks like something is broken in Nova.'
        try:
            resp, body = self.limits_client.get_absolute_limits()
        except Exception as exc:
            base.error(exc)
            self.fail("Step 1 failed: " + fail_msg)
        self.verify_response_status(resp.status, 'Nova', fail_msg, 2)
        self.verify_response_body(body["limits"], u'absolute', fail_msg, 3)
