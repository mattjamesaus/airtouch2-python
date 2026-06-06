import unittest
from airtouch2.common.Buffer import Buffer
from airtouch2.protocol.at2.message_common import checksum, add_checksum_message_buffer


class TestAt2MessageCommon(unittest.TestCase):
    def test_checksum(self):
        self.assertEqual(checksum(bytearray([1, 2, 3, 4])), 10)

    def test_add_checksum_message_buffer(self):
        buffer = Buffer(4)
        buffer.append_bytes(bytes([1, 2, 3]))
        buffer.append_bytes(bytes([0]))
        add_checksum_message_buffer(buffer)
        self.assertEqual(buffer.to_bytes(), bytes([1, 2, 3, 6]))
