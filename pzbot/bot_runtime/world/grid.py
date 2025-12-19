import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from bot_runtime.ingest.state import Tile as StateTile

@dataclass
class GridTile:
    x: int
    y: int
    z: int
    is_walkable: bool = True
    last_seen: float = 0.0

class SpatialGrid:
    """
    Persistent map of the world.
    Aggregates vision data to track visited/walkable tiles.
    """
    def __init__(self):
        # Map (x, y, z) -> GridTile
        self._grid: Dict[Tuple[int, int, int], GridTile] = {}

    def update(self, vision_tiles: List[StateTile]):
        """
        Merges new vision data into the persistent grid.
        Assumes all tiles in 'vision_tiles' are walkable.
        """
        now = time.time()
        for vt in vision_tiles:
            key = (vt.x, vt.y, vt.z)
            if key in self._grid:
                self._grid[key].last_seen = now
            else:
                self._grid[key] = GridTile(
                    x=vt.x,
                    y=vt.y,
                    z=vt.z,
                    is_walkable=True,
                    last_seen=now
                )

    def get_tile(self, x: int, y: int, z: int) -> Optional[GridTile]:
        return self._grid.get((x, y, z))

    def get_stats(self) -> Dict[str, int]:
        return {
            "total_tiles": len(self._grid)
        }
