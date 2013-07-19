from nose.plugins.attrib import attr
from nose.tools import timed

from fuel_health.tests.smoke import base


""" Test module contains tests for flavor creation/deletion. """


class FlavorsAdminTest(base.BaseComputeAdminTest):
    """Tests for flavor creation that require admin privileges."""

    _interface = 'json'

    @attr(type=["fuel", "smoke"])
    @timed(10.9)
    def test_create_flavor(self):
        """Flavor creation
        Target component: Nova

        Scenario:
            1. Create small-size flavor.
            2. Check response status equals 200.
            3. Check created flavor has expected name.
            4. Check flavor disk has expected size.
            5. Check flavor contains 'id' section.
        Duration: 0.5-10.9 s.
        """
        try:
            resp, flavor = self.create_flavor(ram=255,
                                              disk=1)
        except Exception as e:
            base.LOG.error("Low requirements flavor creation failed: %s" % e)
            self.fail("Step 1: Create new volume failed.")

        self.verify_response_status(
            resp.status, appl="Nova")
        self.verify_response_body(
            flavor['name'], u'ost1_test-flavor',
            msg="Flavor name is not the same as requested.")
        self.verify_response_body_value(
            flavor['disk'], 1,
            msg="Disk size is not the same as requested.")
        self.verify_response_body(
            flavor, 'id',
            msg="Flavor was not created properly."
                "Please, check Nova.")
