import unittest
from airtouch2.protocol.at2.lookups import GATEWAYID_BRAND_LOOKUP
from airtouch2.protocol.at2.enums import ACBrand


class TestLookups(unittest.TestCase):
    def test_gateway_brand_lookup_has_expected_values(self):
        self.assertEqual(GATEWAYID_BRAND_LOOKUP[0x8], ACBrand.DAIKIN)
        self.assertEqual(GATEWAYID_BRAND_LOOKUP[0xD], ACBrand.FUJITSU)
        self.assertEqual(GATEWAYID_BRAND_LOOKUP[0xF], ACBrand.MITSUBISHI_ELECTRIC)
