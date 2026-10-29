"""Baseline test suite for parsethon."""

import unittest
import parsethon
import expose_interface


class TestSmoke(unittest.TestCase):
    def test_parsethon_import(self):
        self.assertIsNotNone(parsethon)

    def test_expose_interface_import(self):
        self.assertIsNotNone(expose_interface)


if __name__ == "__main__":
    unittest.main()
