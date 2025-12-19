
import heapq
import math
from typing import List, Tuple, Optional, Set
from .grid import SpatialGrid

class Pathfinder:
    """
    Implements A* pathfinding on the SpatialGrid.
    """
    def __init__(self, grid: SpatialGrid):
        self.grid = grid

    def find_path(self, start: Tuple[int, int, int], end: Tuple[int, int, int]) -> Optional[List[Tuple[int, int, int]]]:
        """
        Calculates a path from start to end using A*.
        Returns a list of coordinates including start and end, or None if no path found.
        """
        # Trivial case
        if start == end:
            return [start]
            
        # If target isn't walkable, we can't search (basic check)
        # Note: In partial exploration, we might want to path to the 'nearest known' tile,
        # but for now let's assume strict A*.
        # if not self.grid.is_walkable(*end):
        #    return None
        
        open_set = []
        heapq.heappush(open_set, (0, start))
        
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._heuristic(start, end)}
        
        visited: Set[Tuple[int, int, int]] = set()

        while open_set:
            current = heapq.heappop(open_set)[1]

            if current == end:
                return self._reconstruct_path(came_from, current)

            visited.add(current)

            # Get neighbors via Grid
            neighbors = self.grid.get_neighbors(*current)
            for neighbor in neighbors:
                neighbor_pos = (neighbor.x, neighbor.y, neighbor.z)
                
                if neighbor_pos in visited:
                    continue

                # Calculate tentative G Score
                # Verify diagonal vs cardinal cost
                dist = math.sqrt((current[0]-neighbor.x)**2 + (current[1]-neighbor.y)**2)
                tentative_g_score = g_score[current] + dist

                if neighbor_pos not in g_score or tentative_g_score < g_score[neighbor_pos]:
                    came_from[neighbor_pos] = current
                    g_score[neighbor_pos] = tentative_g_score
                    f = tentative_g_score + self._heuristic(neighbor_pos, end)
                    f_score[neighbor_pos] = f
                    heapq.heappush(open_set, (f, neighbor_pos))
                    
        return None

    def _heuristic(self, a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
        """Euclidean distance for heuristic."""
        return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2 + (a[2] - b[2])**2)

    def _reconstruct_path(self, came_from: dict, current: Tuple[int, int, int]) -> List[Tuple[int, int, int]]:
        total_path = [current]
        while current in came_from:
            current = came_from[current]
            total_path.append(current)
        return total_path[::-1]
