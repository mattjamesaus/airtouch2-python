import unittest

from airtouch2.protocol.at2plus.messages.AuxSensorStatus import AuxSensorStatusMessage


class TestAuxSensorStatusMessage(unittest.TestCase):
    def test_from_bytes_parses_six_records(self):
        raw = bytes([
            0x80, 0x80, 0x07, 0xFF,
            0x81, 0x81, 0x07, 0xFF,
            0x82, 0x82, 0x07, 0xFF,
            0x83, 0x83, 0x07, 0xFF,
            0x90, 0xFF, 0x02, 0xC2,
            0x91, 0xFF, 0x07, 0xFF,
        ])
        message = AuxSensorStatusMessage.from_bytes(raw)
        self.assertEqual(len(message.statuses), 6)

        self.assertEqual(message.statuses[0].sensor_id, 0x80)
        self.assertEqual(message.statuses[0].associated_id, 0x80)
        self.assertIsNone(message.statuses[0].temperature)
        self.assertEqual(message.statuses[0].raw_temperature, 0x07FF)

        self.assertEqual(message.statuses[4].sensor_id, 0x90)
        self.assertIsNone(message.statuses[4].associated_id)
        self.assertAlmostEqual(message.statuses[4].temperature, 20.6)
        self.assertEqual(message.statuses[4].raw_temperature, 0x02C2)

        self.assertEqual(message.statuses[5].sensor_id, 0x91)
        self.assertIsNone(message.statuses[5].associated_id)
        self.assertIsNone(message.statuses[5].temperature)
        self.assertEqual(message.statuses[5].raw_temperature, 0x07FF)

    def test_from_bytes_rejects_non_multiple_of_four(self):
        raw = bytes([0x80, 0x80, 0x07])
        with self.assertRaises(ValueError):
            AuxSensorStatusMessage.from_bytes(raw)
