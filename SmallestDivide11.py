#!/usr/bin/env python3

import unittest

#
# name: solution
# author: ericp
# descr: return smallest multiple of 11 from an array of integers
#        expected array length between 1 and 1000
#        expected values between -10,000 and 10,000
def solution(input):
    # type check for list
    if type(input) != list:
        raise ValueError("expected list of integers as input")
    new_list = []
    # iterate over list return values evenly divisable by 11
    for number in input:
        if number % 11 == 0:
            new_list.append(number)
    # Please write your code here.
    if new_list:
        return min(new_list)
    else:
        return None

def smallest_eleven(input):
    # type check for list
    if type(input) != list:
        raise ValueError("expected list of integers as input")
    # iterate over list return values evenly divisable by 11
    new_list = list(filter(lambda number: number % 11 == 0, input))
    # Please write your code here.
    if new_list:
        return min(new_list)
    else:
        return None

class TestSolution(unittest.TestCase):
    def test_solution(self):
        self.assertEqual(smallest_eleven([-6, -91, 1011, -100, 84, -22, 0, 1, 473]),-22)
        self.assertEqual(smallest_eleven([-11,22]),-11)
        self.assertEqual(smallest_eleven([11,22]),11)
        self.assertEqual(smallest_eleven([11]),11)

    def test_big_range(self):
        self.assertEqual(smallest_eleven([-10000,-1000,-22,1000,10000]),-22)
        self.assertEqual(smallest_eleven([-11000,-1000,-22,1000,10000]),-11000)
        self.assertEqual(smallest_eleven([-10000,-1000,-25,11000,10000]),11000)

    def test_empty(self):
        self.assertEqual(smallest_eleven([1,2,3,4]),None)

    # python is loos with types, don't want it to accidently work on invalid types
    def test_valid_type(self):
        with self.assertRaises(ValueError):
            smallest_eleven("abc")

unittest.main(exit=False)
