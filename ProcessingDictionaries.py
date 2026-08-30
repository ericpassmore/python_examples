#!/usr/bin/env python3

from collections import Counter

print ("Starting")
statuses = {
    "Alice" : "offline",
    "Eric" : "online",
    "Phil" : "online",
}

def online_count(statuses):
    new_dict = [key for key, value in statuses.items() if value == "online"]
    return len(new_dict)

my_dict = online_count(statuses)
status_occurance = {
    status: list(statuses.values()).count(status)
    for status in set(statuses.values())
}

x = [1,2,3,4,1,2,6,7,82,7,1,4]
print (list(dict.fromkeys(x)))
print(dict(Counter(x)))