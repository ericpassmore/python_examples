#!/usr/bin/env python3

print ("starting")

def add_dots(string):
  return ".".join(string)

def remove_dots(string):
  return string.replace(".","")

print ("full test acid: ", remove_dots(add_dots("acid")))
print ("full test test: ", remove_dots(add_dots("test")))

print ("add dots acid: ", add_dots("acid"))
print ("remove dots a.c.i.d: ", remove_dots("a.c.i.d"))
