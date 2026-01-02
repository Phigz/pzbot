from typing import Dict, Any, Optional, Set, List
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
    is_walkable: bool = Field(default=True, alias='w')
    is_explored: bool = False
    
    # Timestamp of last observation
    last_seen: int = Field(default_factory=lambda: int(time.time() * 1000))
    
    # Visualization properties
    layer: Optional[str] = None
    room: Optional[str] = None
    
    # Extensible metadata (store anything else here without changing schema)
    meta: Dict[str, Any] = Field(default_factory=dict)

# --- Schema Definitions for Properties ---
class AnimalProperties(BaseModel):
    species: str
    breed: Optional[str] = None
    age: Optional[int] = None
    health: Optional[float] = None
    isFemale: Optional[bool] = None
    hunger: Optional[float] = 0.0
    thirst: Optional[float] = 0.0
    size: Optional[float] = None
    milking: Optional[bool] = False
    isPetable: Optional[bool] = False
    canBePet: Optional[bool] = False
    canBeAttached: Optional[bool] = False

class ZombieProperties(BaseModel):
    state: Optional[str] = None
    worn: List[str] = Field(default_factory=list)
    weapon: Optional[str] = None

class PlayerProperties(BaseModel):
    username: Optional[str] = None
    state: Optional[str] = None
    worn: List[str] = Field(default_factory=list)
    weapon: Optional[str] = None

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
    # Ideally validates against specific Property models above where possible
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
