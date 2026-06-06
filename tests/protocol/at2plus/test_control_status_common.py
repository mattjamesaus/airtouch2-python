import unittest

from airtouch2.protocol.at2plus.control_status_common import ControlStatusSubType, SubDataLength, ControlStatusSubHeader

class TestSubDataLength(unittest.TestCase):
    def test_serialize(self):
        sdl = SubDataLength(1, 5, 2)
        serialized = sdl.to_bytes()
        expected = (1).to_bytes(2, 'big') + (2).to_bytes(2, 'big') + (5).to_bytes(2, 'big')
        self.assertEqual(serialized, expected)

    def test_deserialize(self):
        raw = (1).to_bytes(2, 'big') + (2).to_bytes(2, 'big') + (5).to_bytes(2, 'big')
        sdl = SubDataLength.from_bytes(raw)
        serialized = sdl.to_bytes()
        self.assertEqual(raw, serialized)

class TestSubHeader(unittest.TestCase):
    def test_serialize(self):
        sdl = SubDataLength(2, 3, 2)
        subheader =ControlStatusSubHeader(ControlStatusSubType.GROUP_CONTROL, sdl)
        serialized = subheader.to_bytes()
        expected = bytes([ControlStatusSubType.GROUP_CONTROL, 0]) + sdl.to_bytes()
        self.assertEqual(serialized, expected)

    def test_aux_sensor_status_subtype(self):
        self.assertEqual(ControlStatusSubType.AUX_SENSOR_STATUS, 0x2B)

    def test_from_bytes_preserves_raw_sub_type(self):
        raw = bytes([0x99, 0, 0, 0, 0, 0, 0, 0])
        subheader = ControlStatusSubHeader.from_bytes(raw)
        self.assertEqual(subheader.sub_type, ControlStatusSubType.UNSET)
        self.assertEqual(subheader.raw_sub_type, 0x99)