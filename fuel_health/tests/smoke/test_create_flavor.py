import logging

from nose.plugins.attrib import attr
from nose.tools import timed

from fuel_health import nmanager


LOG = logging.getLogger(__name__)

""" Test module contains tests for flavor creation/deletion. """


class FlavorsAdminTest(nmanager.SmokeChecksTest):
    """Tests for flavor creation that require admin privileges."""

    _interface = 'json'

    @attr(type=["fuel", "smoke"])
    @timed(10.9)
    def test_create_flavor(self):
        """Test check that low requirements flavor can be created.
        Target component: Nova

        Scenario:
            1. Create small-size flavor.
            2. Check created flavor has expected name.
            3. Check flavor disk has expected size.
        Duration: 0.5-10.9 s.
        """
        fail_msg = ("Flavor was not created properly."
                    "Please, check Nova.")
        try:
           flavor = self._create_flavors(self.compute_client, 225, 1)
        except Exception as exc:
            LOG.debug(exc)
            self.fail('Step 1 failed: ' + fail_msg)
        msg_s2 = "Flavor name is not the same as requested."
        self.verify_response_true(
            flavor.name.startswith('ost1_test-flavor'),
            'Step 2 failed: ' + msg_s2)

        msg_s3 = "Disk size is not the same as requested."
        self.verify_response_body_value(
            flavor.disk, 1,
            "Step 3 failed: " + msg_s3)
