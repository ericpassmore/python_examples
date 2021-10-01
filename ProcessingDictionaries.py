#!/usr/bin/env python3

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
print (my_dict)
