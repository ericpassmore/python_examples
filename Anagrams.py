#!/usr/bin/env python3

#from typing import List, Set, Dict, Tuple, Optional
import unittest



def sort_string(string):
   assert type(string) == str
   return "".join(sorted([letter for letter in string]))

def is_anagram(first_param, second_param):
  first_param = sorted(first_param)
  second_param = sorted(second_param)
  return first_param == second_param


# harder solution:
# count how many times each letter appears in each string,
# and make sure all the counts are the same.
def count_letters(string):
    return {l: string.count(l) for l in string}
def is_anagram2(string1, string2):
    return count_letters(string1) == count_letters(string2)


class TestIsAnagram(unittest.TestCase):
    def test_count_letters(self):
        self.assertEqual(count_letters("foo"), {"f":1,"o":2})

    def test_is_anagram(self):
        self.assertTrue(is_anagram2("3weulb","bluew3"))
        self.assertFalse(is_anagram2("foobar","bluew3"))

unittest.main(exit=False)
