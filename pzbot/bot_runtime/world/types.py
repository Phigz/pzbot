from typing import Dict, Any, Optional, Set
from pydantic import BaseModel, Field
import time

class TileData(BaseModel):
    """
    Represents the persistent state of a single tile in the world.
    Designed to be extensible with additional properties (e.g., loot, heatmaps).
    """
    x: int
    y: int
    z: int
    
    # Navigation properties
    is_walkable: bool = True
    is_explored: bool = False
    
    # Timestamp of last observation
    last_seen: int = Field(default_factory=lambda: int(time.time() * 1000))
    
    # Visualization properties
    layer: Optional[str] = None
    room: Optional[str] = None
    
    # Extensible metadata (store anything else here without changing schema)
    meta: Dict[str, Any] = Field(default_factory=dict)

class EntityData(BaseModel):
    """
    Represents a dynamic entity (Zombie, Player, Vehicle) tracked over time.
    """
    id: str
    type: str
    
    # Last known position
    x: float
    y: float
    z: float
    
    # Tracking
    last_seen: int = Field(default_factory=lambda: int(time.time() * 1000))
    is_visible: bool = True
    
    # Extensible properties (health, weapons, behavior state)
    properties: Dict[str, Any] = Field(default_factory=dict)

class VehicleData(EntityData):
    """
    Specialized entity for Vehicles with mechanical state.
    """
    pass # Properties stored in 'properties' dict for flexibility, but typed class helps distinction

class GridChunkData(BaseModel):
    """
    Represents a 10x10 chunk of the world grid.
    """
    chunk_x: int
    chunk_y: int
    tiles: Dict[str, TileData] = Field(default_factory=dict) # Key: "x_y_z"
    last_visited: int = Field(default_factory=lambda: int(time.time() * 1000))
