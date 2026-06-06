import unittest
from airtouch2.protocol.at2plus import conversions
from airtouch2.protocol.at2plus.constants import Limits


class TestConversions(unittest.TestCase):
    def test_setpoint_round_trip(self):
        self.assertEqual(conversions.setpoint_from_value(conversions.value_from_setpoint(22.5)), 22.5)

    def test_setpoint_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            conversions.value_from_setpoint(Limits.SETPOINT_MAX + 10)

    def test_setpoint_none_returns_expected_marker(self):
        expected = int(Limits.SETPOINT_MAX * 10 - 100 + 1)
        self.assertEqual(conversions.value_from_setpoint(None), expected)

    def test_temperature_round_trip(self):
        self.assertEqual(conversions.temperature_from_value(conversions.value_from_temperature(20.0)), 20.0)

    def test_temperature_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            conversions.value_from_temperature(Limits.TEMP_MAX + 10)

    def test_temperature_none_returns_marker(self):
        expected = int(Limits.TEMP_MAX * 10 + 501)
        self.assertEqual(conversions.value_from_temperature(None), expected)
