import unittest
from airtouch2.common.interfaces import add_callback


class TestInterfaces(unittest.TestCase):
    def test_add_callback_returns_unsubscribe(self):
        results = []
        callbacks = []

        def callback():
            results.append(True)

        remove = add_callback(callback, callbacks)
        self.assertEqual(len(callbacks), 1)

        callbacks[0]()
        self.assertEqual(results, [True])

        remove()
        self.assertEqual(callbacks, [])
