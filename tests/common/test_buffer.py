import unittest
from airtouch2.common.Buffer import Buffer
from airtouch2.common.interfaces import Serializable


class DummySerializable(Serializable):
    def __init__(self, payload: bytes):
        self._payload = payload

    def to_bytes(self) -> bytes:
        return self._payload


class TestBuffer(unittest.TestCase):
    def test_fill_and_serialize(self):
        buffer = Buffer(4)

        self.assertFalse(buffer.append_bytes(b"ab"))
        self.assertTrue(buffer.append_bytes(b"cd"))
        self.assertEqual(buffer.to_bytes(), b"abcd")

    def test_from_bytes_preserves_data(self):
        result = Buffer.from_bytes(b"test")
        self.assertEqual(result.to_bytes(), b"test")

    def test_read_bytes_and_remaining(self):
        buffer = Buffer(4)
        buffer.append_bytes(b"abcd")

        self.assertEqual(buffer.read_bytes(2), b"ab")
        self.assertEqual(buffer.read_remaining(), b"cd")
        with self.assertRaises(BufferError):
            buffer.read_bytes(1)

    def test_read_bytes_oversize_raises(self):
        buffer = Buffer(4)
        buffer.append_bytes(b"abcd")

        with self.assertRaises(BufferError):
            buffer.read_bytes(5)

    def test_append_object(self):
        buffer = Buffer(2)
        self.assertTrue(buffer.append(DummySerializable(b"xy")))
        self.assertEqual(buffer.to_bytes(), b"xy")

    def test_errors_for_overflow_and_incomplete_buffer(self):
        buffer = Buffer(2)
        with self.assertRaises(BufferError):
            buffer.append_bytes(b"abc")

        buffer = Buffer(2)
        buffer.append_bytes(b"a")
        with self.assertRaises(BufferError):
            buffer.to_bytes()
        with self.assertRaises(BufferError):
            buffer.read_bytes(1)
