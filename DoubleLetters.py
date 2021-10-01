#!/usr/bin/env python3

print ("starting")

def double_letters_simple(string):
    for i in range(len(string) - 1):
        letter1 = string[i]
        letter2 = string[i+1]
        if letter1 == letter2:
            return True
    return False

def double_letters_with_zip(word):
    return any([a == b for a, b in (zip(word, word[1:]))])

def double_letters(word):
  is_double = False
  previous_letter = None
  for letter in word:
    print (letter)
    if previous_letter is not None and \
         previous_letter == letter:
       is_double = True
       break
    previous_letter = letter
  return is_double


print ("fist: ", double_letters_with_zip("first"))
print ("hello: ", double_letters_with_zip("hello"))
print ("nono: ", double_letters_with_zip("nono"))
