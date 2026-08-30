#!/usr/bin/env python3

from collections import Counter

ItemName = '''
Unique values in string ['b', 'a', 'n']
Counter occurances in string {'b': 1, 'a': 3, 'n': 3}
Max occurance in string a
Third Most Common ('n', 3)
Third Least Common ('a', 3)
'''
counts = Counter(ItemName)

print (f'Unique values in string {list(dict.fromkeys(ItemName))}')
print (f'Counter occurances in string {dict(counts)}')
print (f'Max occurance in string {max(counts, key=counts.get)}')

print (f'Second Most Common {counts.most_common(2)[1]}')
print(f'Second Least Common {counts.most_common()[:-2-1:-1][1]}')