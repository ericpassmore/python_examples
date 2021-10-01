#!/usr/bin/python3

import unittest

def simple(lists_to_merge):
    if type(lists_to_merge) != list:
        raise ValueError("expected list")
    return [1,2,3,4]

class TestSimple(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(simple([[1,2],[3,4]]), [1,2,3,4])

    def test_is_working(self):
        self.assertTrue(type(simple([[1,2],[3,4]])) == list)

    def test_correct_types(self):
        with self.assertRaises(ValueError):
            simple("abc")

unittest.main(exit=False)
