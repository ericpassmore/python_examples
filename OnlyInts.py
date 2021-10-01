#!/usr/bin/env python3

def only_ints(first_param, second_param):
  return isinstance(first_param, int)      and \
         isinstance(second_param, int)     and \
         not isinstance(first_param, bool) and \
         not isinstance(second_param, bool)

print ("try 1,1: ", only_ints(1,1))
print ("try a,1: ", only_ints("a",1))
print ("try 1,a: ", only_ints(1,"a"))
print ("try 1,2: ", only_ints(1,2))
print ("try 2,6: ", only_ints(2,6))
print ("try 1, True: ", only_ints(1,True))
