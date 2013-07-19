import logging
from nose.plugins.attrib import attr
from nose.tools import timed

from fuel_health import nmanager

LOG = logging.getLogger(__name__)


class SanityComputeTest(nmanager.SanityChecksTest):
    """
    TestClass contains tests check base Compute functionality.
    """
    _interface = 'json'

    @attr(type=['sanity', 'fuel'])
    @timed(5.5)
    def test_list_instances(self):
        """Test checks that list of instances is available.
        Target component: Nova
        Scenario:
            1. Request list of instances.
            2. Check response.
        Duration: 0.6-5.6 s.
        """
        fail_msg = ('Servers list is unavailable. '
                    'Looks like something is broken in Nova.')
        try:
            list_instance_resp = self._list_instances(
                self.compute_client)
        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 1 failed: " + fail_msg)

        self.verify_response_true(
            len(list_instance_resp) >= 0, "Step 2 failed: " + fail_msg)

    @attr(type=['sanity', 'fuel'])
    @timed(5.5)
    def test_list_images(self):
        """Test checks that list of images is available.
        Target component: Glance
        Scenario:
            1. Request list of images.
            2. Check response.
        Duration: 0.8-5.6 s.
        """
        fail_msg = ('Images list is unavailable. '
                    'Looks like something is broken in Nova or Glance.')
        try:
            list_images_resp = self._list_images(
                self.compute_client)
        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 1 failed: " + fail_msg)

        self.verify_response_true(
            len(list_images_resp) >= 0, "Step 2 failed: " + fail_msg)


    @attr(type=['sanity', 'fuel'])
    @timed(5.5)
    def test_list_volumes(self):
        """Test checks that list of volumes is available.
        Target component: Swift

        Scenario:
            1. Request list of volumes.
            2. Check response.
        Duration: 0.6-5.6 s.
        """
        fail_msg = ('Volumes list is unavailable. '
                    'Looks like something is broken in Nova or Cinder.')
        try:
            list_volumes_resp = self._list_volumes(
                self.volume_client)
        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 1 failed: " + fail_msg)

        self.verify_response_true(
            len(list_volumes_resp) >= 0, "Step 2 failed: " + fail_msg)

    @attr(type=['sanity', 'fuel'])
    @timed(5.5)
    def test_list_snapshots(self):
        """Test checks that list of snapshots is available.
        Target component: Glance

        Scenario:
            1. Request list of snapshots.
            2. Check response.
        Duration: 0.9-5.6 s.
        """
        fail_msg = ('Snapshots list is unavailable. '
                    'Looks like something is broken in Nova or Cinder.')
        try:
            list_snapshots_resp = self._list_snapshots(
                self.volume_client)
        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 1 failed: " + fail_msg)

        self.verify_response_true(
            len(list_snapshots_resp) >= 0, "Step 2 failed: " + fail_msg)


    @attr(type=['sanity', 'fuel'])
    @timed(5.5)
    def test_list_flavors(self):
        """Test checks list of flavors is available.
        Target component: Nova

        Scenario:
            1. Request list of flavors.
            2. Check response.
        Duration: 1.2-5.6 s.
        """
        fail_msg = ('Flavors list is unavailable. '
                    'Looks like something is broken in Nova.')
        try:
            list_flavors_resp = self._list_flavors(
                self.compute_client)
        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 1 failed: " + fail_msg)

        self.verify_response_true(
            len(list_flavors_resp) >= 0, "Step 2 failed: " + fail_msg)

    @attr(type=['sanity', 'fuel'])
    @timed(5.5)
    def test_list_rate_limits(self):
        """Test checks that list of absolute limits is available.
        Target component: Nova

        Scenario:
            1. Request list of limits.
            2. Check response.
        Duration: 1.5-5.6 s.
        """
        fail_msg = ('Limits list is unavailable. '
                    'Looks like something is broken in Nova.')
        try:
            list_limits_resp = self._list_limits(
                self.compute_client)

        except Exception as exc:
            LOG.debug(exc)
            self.fail("Step 1 failed: " + fail_msg)

        self.verify_response_true(
            list_limits_resp, "Step 2 failed: " + fail_msg)
