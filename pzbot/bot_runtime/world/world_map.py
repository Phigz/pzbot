import logging
from typing import Dict, Tuple, List, Optional
from .types import TileData

logger = logging.getLogger(__name__)

class WorldMap:
    """
    Manages the persistent grid of the world.
    Stores knowledge about tiles, walls, and traversability.
    """
    def __init__(self):
        # Sparse grid: (x, y, z) -> TileData
        self.grid: Dict[Tuple[int, int, int], TileData] = {}
        
        # Bounds of exploring (for limiting A* search space if needed)
        self.min_x = float('inf')
        self.max_x = float('-inf')
        self.min_y = float('inf')
        self.max_y = float('-inf')

    def update_tile(self, x: int, y: int, z: int, is_walkable: bool = True, meta: dict = None):
        """Updates or creates a tile in the map."""
        key = (x, y, z)
        
        if key not in self.grid:
            self.grid[key] = TileData(x=x, y=y, z=z, is_walkable=is_walkable)
            self._update_bounds(x, y)
        else:
            tile = self.grid[key]
            tile.is_walkable = is_walkable
            tile.last_seen = int(time.time() * 1000)
            if meta:
                tile.meta.update(meta)
        
        self.grid[key].is_explored = True

    def get_tile(self, x: int, y: int, z: int) -> Optional[TileData]:
        return self.grid.get((x, y, z))

    def _update_bounds(self, x: int, y: int):
        self.min_x = min(self.min_x, x)
        self.max_x = max(self.max_x, x)
        self.min_y = min(self.min_y, y)
        self.max_y = max(self.max_y, y)

    def import_vision(self, tiles: List[dict]):
        """
        Ingests a list of visible tiles from the bot's sensor.
        Expected format: {'x': 1, 'y': 2, 'z': 0} (assumed walkable if in 'tiles' list)
        """
        import time # Lazy import if needed or rely on module level
        
        # Note: The 'vision.tiles' list usually contains WALKABLE tiles.
        # We might need to infer walls if we see adjacent blocked nodes in the future.
        # For now, we mark these as walkable.
        for t in tiles:
            # t is a Pydantic Tile object from state.py
            self.update_tile(t.x, t.y, t.z, is_walkable=True)

import time
