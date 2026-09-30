from typing import List

class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        seen = {}

        for index, value in enumerate(nums):
            compliment = target - value
            if compliment in seen:
                return [seen[compliment],index]
            seen[value] = index


mysolution = Solution()
nums = [ 1,2,3,4,5,6]
target = 9
out = mysolution.twoSum(nums,target)
assert [3,4] == out, f"expected [3,4] result {out}"
