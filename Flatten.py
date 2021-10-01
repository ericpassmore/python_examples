#!/usr/bin/python3

import unittest
import itertools

def flatten(lists_to_merge):
    return list(itertools.chain.from_iterable(lists_to_merge))

class TestFlatten(unittest.TestCase):
    def test_flatten(self):
        self.assertEqual(flatten([[1,2],[3,4]]), [1,2,3,4])

    def test_is_list(self):
        self.assertTrue(type(flatten([[1,2],[3,4]])) == list)

unittest.main(exit=False)
