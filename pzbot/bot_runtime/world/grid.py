import time
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from bot_runtime.ingest.state import Tile as StateTile

logger = logging.getLogger(__name__)

@dataclass
class GridTile:
    x: int
    y: int
    z: int
    is_walkable: bool = True
    last_seen: float = 0.0
    room: Optional[str] = None
    layer: Optional[str] = None

class SpatialGrid:
    """
    Persistent map of the world.
    Aggregates vision data to track visited/walkable tiles.
    """
    def __init__(self):
        # Map (x, y, z) -> GridTile
        self._grid: Dict[Tuple[int, int, int], GridTile] = {}
        
        # World Bounds
        self.min_x = float('inf')
        self.max_x = float('-inf')
        self.min_y = float('inf')
        self.max_y = float('-inf')

    def update(self, vision_tiles: List[StateTile]):
        """
        Merges new vision data into the persistent grid.
        Assumes all tiles in 'vision_tiles' are walkable.
        """
        now = time.time()
        new_tiles_count = 0
        
        for vt in vision_tiles:
            key = (vt.x, vt.y, vt.z)
            if key in self._grid:
                tile = self._grid[key]
                tile.last_seen = now
                tile.is_walkable = True
                if vt.room:
                    tile.room = vt.room
                if vt.layer:
                    tile.layer = vt.layer
            else:
                self._grid[key] = GridTile(
                    x=vt.x,
                    y=vt.y,
                    z=vt.z,
                    is_walkable=True,
                    last_seen=now,
                    room=vt.room,
                    layer=vt.layer
                )
                self._update_bounds(vt.x, vt.y)
                new_tiles_count += 1

        if new_tiles_count > 0:
            logger.debug(f"Grid updated: +{new_tiles_count} new tiles. Total: {len(self._grid)}")

    def _update_bounds(self, x: int, y: int):
        self.min_x = min(self.min_x, x)
        self.max_x = max(self.max_x, x)
        self.min_y = min(self.min_y, y)
        self.max_y = max(self.max_y, y)

    def get_tile(self, x: int, y: int, z: int) -> Optional[GridTile]:
        return self._grid.get((x, y, z))

    def is_walkable(self, x: int, y: int, z: int) -> bool:
        """Returns True if the tile is known and walkable."""
        t = self.get_tile(x, y, z)
        return t is not None and t.is_walkable

    def get_neighbors(self, x: int, y: int, z: int) -> List[GridTile]:
        """Returns adjacent walkable tiles (N, S, E, W, and diagonals)."""
        neighbors = []
        # 8-directional movement
        deltas = [
            (0, 1), (0, -1), (1, 0), (-1, 0),
            (1, 1), (1, -1), (-1, 1), (-1, -1)
        ]
        
        for dx, dy in deltas:
            nx, ny = x + dx, y + dy
            if self.is_walkable(nx, ny, z):
                neighbors.append(self.get_tile(nx, ny, z))
                
        return neighbors

    def get_stats(self) -> Dict[str, int]:
        return {
            "total_tiles": len(self._grid),
            "bounds": f"[{self.min_x},{self.min_y}] to [{self.max_x},{self.max_y}]"
        }

    def get_tiles_by_room(self, room_name: str) -> List[GridTile]:
        """Returns all tiles belonging to a specific room."""
        return [
            t for t in self._grid.values() 
            if t.room == room_name
        ]

    def save_snapshot(self, path: str, world_items: List = None, nearby_containers: List = None):
        """Serializes the current grid state to a JSON file."""
        data = {
            "bounds": {
                "min_x": self.min_x if self.min_x != float('inf') else 0,
                "max_x": self.max_x if self.max_x != float('-inf') else 0,
                "min_y": self.min_y if self.min_y != float('inf') else 0,
                "max_y": self.max_y if self.max_y != float('-inf') else 0,
            },
            "tiles": [],
            "world_items": world_items or [],
            "nearby_containers": nearby_containers or []
        }
        
        for tile in self._grid.values():
            data["tiles"].append(asdict(tile))
            
        try:
            with open(path, "w") as f:
                json.dump(data, f)
            logger.info(f"Grid snapshot saved to {path} ({len(self._grid)} tiles, {len(data['world_items'])} items, {len(data['nearby_containers'])} containers)")
        except Exception as e:
            logger.error(f"Failed to save grid snapshot: {e}")
