
import unittest
from typing import List
from bot_runtime.world.grid import SpatialGrid, GridTile
from bot_runtime.world.nav import Pathfinder

# Mock StateTile for ingestion
class MockTile:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class TestNavigation(unittest.TestCase):
    def setUp(self):
        self.grid = SpatialGrid()
        self.nav = Pathfinder(self.grid)

    def test_grid_initialization(self):
        self.assertEqual(len(self.grid._grid), 0)

    def test_simple_path(self):
        # Create a 3x3 open room
        tiles = []
        for x in range(3):
            for y in range(3):
                tiles.append(MockTile(x, y, 0))
        self.grid.update(tiles)
        
        path = self.nav.find_path((0, 0, 0), (2, 2, 0))
        self.assertIsNotNone(path)
        self.assertEqual(path[0], (0, 0, 0))
        self.assertEqual(path[-1], (2, 2, 0))

    def test_obstacle_avoidance(self):
        # Create a grid with a wall
        # S . .
        # W W .
        # T . .
        tiles = []
        for x in range(3):
            for y in range(3):
                # Wall at (1, 1) and (0, 1)
                if y == 1 and x <= 1: 
                    continue
                tiles.append(MockTile(x, y, 0))
        self.grid.update(tiles)

        # Start (0,0), Target (0,2) -> Should go around the wall at y=1
        start = (0, 0, 0)
        target = (0, 2, 0)
        
        path = self.nav.find_path(start, target)
        self.assertIsNotNone(path)
        
        # Ensure we didn't walk through the wall (0,1) or (1,1)
        for node in path:
            self.assertFalse(node == (0, 1, 0))
            self.assertFalse(node == (1, 1, 0))

    def test_no_path(self):
        # Disconnected areas
        self.grid.update([MockTile(0, 0, 0), MockTile(10, 10, 0)])
        
        path = self.nav.find_path((0, 0, 0), (10, 10, 0))
        self.assertIsNone(path)

if __name__ == '__main__':
    unittest.main()
