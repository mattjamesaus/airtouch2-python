import io
import unittest
from contextlib import redirect_stdout

from airtouch2.helpers.diff_bytes import split_hex_in_words, print_diff_with_addresses


class TestDiffBytes(unittest.TestCase):
    def test_split_hex_in_words_chunks_hex_data(self):
        data = "".join(["{:02x}".format(i) for i in range(32)])
        lines = split_hex_in_words(data)

        self.assertTrue(lines)
        self.assertTrue(all("\t" in line for line in lines))

    def test_print_diff_with_addresses_outputs_marked_diff(self):
        old_bytes = b"hello world"
        new_bytes = b"hello worle"
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            print_diff_with_addresses(old_bytes, new_bytes)

        output = buffer.getvalue()
        self.assertIn("-", output)
        self.assertIn("+", output)
