import unittest
from bot_runtime.world.grid import SpatialGrid, GridTile
from bot_runtime.ingest.state import Tile as StateTile

class TestSpatialGrid(unittest.TestCase):
    def test_update_adds_new_tiles(self):
        grid = SpatialGrid()
        
        # Initial stats
        self.assertEqual(grid.get_stats()["total_tiles"], 0)
        
        # New vision
        vision_tiles = [
            StateTile(x=10, y=10, z=0),
            StateTile(x=11, y=10, z=0)
        ]
        
        grid.update(vision_tiles)
        
        self.assertEqual(grid.get_stats()["total_tiles"], 2)
        tile = grid.get_tile(10, 10, 0)
        self.assertIsNotNone(tile)
        self.assertEqual(tile.x, 10)
        self.assertTrue(tile.is_walkable)

    def test_update_updates_timestamp(self):
        grid = SpatialGrid()
        vision_tiles = [StateTile(x=10, y=10, z=0)]
        grid.update(vision_tiles)
        
        t1 = grid.get_tile(10, 10, 0).last_seen
        
        # Simulate slight delay
        import time; time.sleep(0.01)
        
        grid.update(vision_tiles)
        t2 = grid.get_tile(10, 10, 0).last_seen
        
        self.assertGreater(t2, t1)

    def test_update_merges_unique_tiles(self):
        grid = SpatialGrid()
        grid.update([StateTile(x=10, y=10, z=0)])
        grid.update([StateTile(x=11, y=10, z=0)]) # New tile
        grid.update([StateTile(x=10, y=10, z=0)]) # Existing tile
        
        self.assertEqual(grid.get_stats()["total_tiles"], 2)

if __name__ == '__main__':
    unittest.main()
