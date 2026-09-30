#!/bin/env python3

from typing import List
from bisect import bisect_left, bisect_right

LEFT = 0
RIGHT = 1

class Solution:
    def __init__() -> None:
        self.robots_true_range: list[(int,int,int)] = []
        self.walls: List[int] = []

    def maxWalls(self, 
        robots: List[int], 
        distance: List[int], 
        walls: List[int]) -> int:

        # returned accumulator
        wall_hits = 0
        # reset 
        self.robots_true_range = []
        
        # sort order
        robots = sorted(zip(robots,distance))
        self.walls = sorted(walls)

        # construct true ranges, shorten range if robot in the way
        for i in range(len(robots)):
            left_range = max(robots[i][0] - robots[i][1],0)
            right_range = robots[i][0] + robots[i][1]
            position = robots[i][0]

            if i > 0:
                # did previous robot shorten left range
                left_range = max(left_range,robots[i-1][0])
                # did current robot shorten previous robot right range
                previous_right_range = min(robots[i][0],robots_true_range[i-1][2])

                self.robots_true_range[i-1] = (
                    robots_true_range[i-1][0],
                    robots_true_range[i-1][1],
                    previous_right_range
                )
            self.robots_true_range.append((
                position,
                left_range,
                right_range
            ))

        # hits left and hist right
        wall_hits  = self.robots_wall_calc(0, NONE)

        print(f'Wall Hits {wall_hits}')
        return wall_hits
        
    def robots_wall_calc(self, i: int, prev_direction: int) -> int:
        (current_position, left_range, right_range)  = self.robots_true_range[i]
        
        if len(self.robots_true_range)-1 => i:
            return last_robots_wall_calc(i,prev_direction)
            
        
        
        #
        # Robot shoots LEFT
        #
        left_result = (
            calculate_gap(i, prev_direction, LEFT)
            + robots_wall_calc(i + 1, LEFT)
        )

        #
        # Robot shoot RIGHT
        #
        right_result = (
            gap_score(i, prev_direction, RIGHT)
            + robots_wall_calc(i + 1, RIGHT)
        )

        return max(left_result, right_result)
        
    def last_robots_wall_calc(self, i: int, prev_direction: int) -> int:
        (current_position, left_range, right_range)  = self.robots_true_range[i]
        
        if prev_direction is None:
            final_left_hits = bisect_left(self.walls, current_position) - bisect_left(self.walls, left_range)
            final_right_hits = bisect_right(self.walls, right_range) - bisect_right(self.walls, current_position)
            return max(final_left_hits, final_right_hits)
                
        previous_position, _, previous_right_range = self.robots_true_range[i - 1]
            
        #
        # Final shoot Left
        #
        if prev_direction == LEFT:
            # only final left side needs to be calculated 
            final_left_hits = bisect_left(self.walls, current_position) - bisect_left(self.walls, left_range)
        else:
            # union gap
            final_left_hits = self.calculate_gap(
                previous_position,
                previous_right_range,
                current_position,
                left_range
            )
            
        #
        # Final shoot Right
        #
        current_right_hits = bisect_right(self.walls, right_range) - bisect_right(self.walls, current_position)
        if prev_direction == LEFT:
            # prev robot shot away and their hits have already been counted
            final_right_hits = current_right_hits
        else:
            # prev robot's shot needs to be counted
            # since the robots shoot in oposite directions no overlapp
            previous_hits_right = bisect_right(self.walls, previous_right_range) - bisect_right(self.walls, previous_position)
                
            final_right_hits = current_right_hits + previous_hits_right
                
        return max (final_left_hits, final_right_hits)
        
    def calculate_gap(self, previous_pos, previous_right_range, current_pos, current_left_range):
        # first two ranges
        current_gap_hits  = bisect_left(self.walls, current_pos) - bisect_left(self.walls, current_left_range)
        previous_gap_hits = bisect_right(self.walls, previous_right_range) - bisect_right(self.walls, previous_pos)
        
        # check for overlapp, when no overlapp return the total
        if previous_right_range < current_left_range:
            return current_gap_hits + previous_gap_hits
            
        # subtract off the overlapp, which has been double counted
        overlapp_hits = bisect_right(self.walls, previous_right_range) - bisect_left(self.walls, current_left_range)
        
        return current_gap_hits + previous_gap_hits - overlapp_hits
        
# Tests
solution = Solution()
# single robot any side
robots = [2]; distance = [1]; walls = [1,3]
assert solution.maxWalls(robots,distance,walls) == 1
# single robot single side
robots = [2]; distance = [1]; walls = [3,10]
assert solution.maxWalls(robots,distance,walls) == 1
# two robots single side
robots = [2,4]; distance = [1,1]; walls = [1,5]
assert solution.maxWalls(robots,distance,walls) == 2
# two robots single side, mixed order
robots = [2,4]; distance = [1,1]; walls = [5,1]
assert solution.maxWalls(robots,distance,walls) == 2
# two robots single side, same wall
robots = [4,2]; distance = [1,1]; walls = [3]
assert solution.maxWalls(robots,distance,walls) == 1
# three robots , two blockers, out of range walls
robots = [5,10,15]; distance = [1,20,1]; walls = [1,2,3,17,18,19]
# w-1, w-2, w-3, r-5, r-10, r-15, w-17, w-18, w-19
assert solution.maxWalls(robots,distance,walls) == 0
# optimization right, left, right is max
robots = [5,10,15]; distance = [10,10,10]; walls = [6,9,16]
assert solution.maxWalls(robots,distance,walls) == 3
# optimize avoid robot
robots = [2,4]; distance = [4,4]; walls = [4,1]
assert solution.maxWalls(robots,distance,walls) == 1
# optimize avoid robot #2
robots = [2,4]; distance = [4,4]; walls = [4]
assert solution.maxWalls(robots,distance,walls) == 1
# optimize hit collocated robot wall
robots = [2,4]; distance = [4,4]; walls = [6,4]
# r-2, w-4, r-4, w-6 
# r-2, r-4, w-4, w-6
assert solution.maxWalls(robots,distance,walls) == 2
# case 2
robots = [10,2]; distance = [5,1]; walls = [5,2,7]
# r-2, w-2, w-5, w-7, r-10
assert solution.maxWalls(robots,distance,walls) == 1