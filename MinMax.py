#!/usr/bin/python3

import unittest

def largest_difference(list_of_ints):
    return max(list_of_ints) - min(list_of_ints)

class TestSimple(unittest.TestCase):
    def test_largest_difference(self):
        self.assertEqual(largest_difference([1,2,4]),3)

    def test_largest_difference_is_int(self):
        self.assertTrue(type(largest_difference([2,3,4])) == int)

unittest.main(exit=False)
