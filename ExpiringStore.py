#!/usr/bin/env python3

import time
import heapq
from typing import Any

class _Cache:
	'''
	_Cache holds a dict for fast lookup by value
	along with a heap(list) for keys sotred by expiry time and fast expiration
	'''
	def __init__(self) -> None:
		# cache stores key -> value, expire_at lookup O(1) get
		self.cache: dict[str, tuple[Any, float]] = {}
		# expirations stores ordered expired_at, key
		# set O(log n)
		# count expires old entries O(k log(n)) when k entries are expired
		self.expirations: list[tuple[float, str]] = []

	def __len__(self) -> int:
		'''returns size of cache'''
		return len(self.cache)

	def set(self, key: str, data: Any, expire_at: float) -> None:
		'''
		populated the dict and heap
		Note: set on the same value will create multiple heap entires
		and a single dict entry. The single dict entry returns the correct value
		The heap will get cleaned up lazily
		'''
		self.cache[key] = (data, expire_at)
		heapq.heappush(self.expirations, (expire_at, key))

	def get(self, key: str, current_time: float) -> Any | None:
		'''return the cache, do not return expired entries'''
		cached = self.cache.get(key)
		if cached is None:
			return None
		# good entry return it
		# else remove it, heap cleaned up lazily
		if cached[1] > current_time:
			return cached[0]
		else:
			del self.cache[key]
			return None
			
	def remove(self, key: str) -> None:
		'''remove the cached entry'''
		cached = self.cache.get(key)
		if cached is None:
			return None

		del self.cache[key]

	def compact_before(self, current_time: float) -> list[str]:
		'''Cleanup and removal of expired items from both dict and heap'''
		expired: list[str] = []
		
		while self.expirations:
			# first not-expired value break out, we are complete
			# heap entries are always sorted with earlist first
			if self.expirations and self.expirations[0][0] > current_time:
				break
			
			# always pop and remove expired heap entires
			# check expires matches dict value
			# extenstion could have changed value
			expire_at, key = heapq.heappop(self.expirations)
			cached = self.cache.get(key)
			if cached is not None and expire_at == cached[1]:
				self.remove(key)
				expired.append(key)
		
		return expired

class ExpiringStore():
	def __init__(self) -> None:
		'''Init Expiring Store with _Cache class'''
		self.store = _Cache()
	
	def set(self, key:str, data: Any, ttl_seconds: float) -> None:
		'''Check inputs and store data'''
		if ttl_seconds < 0:
			raise ValueError("ttl_seconds must be non-negative")
		self.store.set(key,data, time.monotonic() + ttl_seconds)
		
	def get(self, key:str) -> Any | None:
		'''get the values'''
		return self.store.get(key, time.monotonic())
		
	def count(self) -> int:
		self.store.compact_before(time.monotonic())
		return len(self.store)

# TESTS 

# create the store
store = ExpiringStore()

# set something and get it back
store.set("session-01","test-val", ttl_seconds=10)
assert store.get("session-01") == "test-val"
assert store.count() == 1

# set something with zero ttl and doesn't come back
store.set("vanished-01","gone", ttl_seconds=0)
assert store.count() == 1
assert store.get("vanished-01") is None

# set ttl with bad value
try:
	store.set("session-02", "test-val", ttl_seconds=-2)
except ValueError:
	pass
else:
	raise Exception("Bad Value Error")
	
# factional ttl
store.set("session-03", "test-val", ttl_seconds=10.2)
assert store.get("session-03") == "test-val"
assert store.count() == 2

# dictionary value
store.set("session-04" , {"user": 52}, 30)
assert store.get("session-04") == {"user": 52}
assert store.count() == 3

# raise timeout
store.set("session-05", "new-val", ttl_seconds=0)
store.set("session-05", "new-val", ttl_seconds=30)
assert store.get("session-05") == "new-val"
assert store.count() == 4

# update value
store.set("session-05", "changed", 30)
assert store.get("session-05") == "changed"
# still same count
assert store.count() == 4