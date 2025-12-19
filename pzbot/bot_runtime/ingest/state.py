from typing import List, Dict, Optional, Any
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

# Removed Vitals as it's no longer in the top-level player object
# class Vitals(BaseModel):
#     health: float = 0.0
#     stamina: float = 0.0
#     hunger: float = 0.0
#     panic: float = 0.0

import logging
from enum import Enum

logger = logging.getLogger(__name__)

class ZombieState(str, Enum):
    IDLE = "IDLE"
    WANDER = "WANDER"
    CHASING = "CHASING"
    ALERTED = "ALERTED"
    ATTACKING = "ATTACKING"
    CRAWLING = "CRAWLING"
    STAGGERING = "STAGGERING"

class LogExtraFieldsBase(BaseModel):
    model_config = ConfigDict(extra='ignore')

    @model_validator(mode='before')
    @classmethod
    def check_for_extra_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Check for keys in data that are not in the model fields
            # We need to handle aliases if they exist, but for now we assume field names match
            # Also need to consider that data might be a subset if fields are optional
            
            allowed_keys = set(cls.model_fields.keys())
            input_keys = set(data.keys())
            extra_keys = input_keys - allowed_keys
            
            if extra_keys:
                logger.warning(f"Ignored extra fields in {cls.__name__}: {extra_keys}")
        return data

class Position(LogExtraFieldsBase):
    x: float
    y: float
    z: float

class PlayerStateFlags(LogExtraFieldsBase):
    aiming: bool = False
    sneaking: bool = False
    running: bool = False
    sprinting: bool = False
    in_vehicle: bool = False
    is_sitting: bool = False
    # Extra fields from util.lua/initialization
    asleep: bool = False
    moving: bool = False
    driving: bool = False
    bumped: bool = False
    climbing: bool = False
    attacking: bool = False

class BodyPart(LogExtraFieldsBase):
    health: float
    bandaged: bool
    bleeding: bool
    bitten: bool
    scratched: bool
    deep_wound: bool
    # Extra fields from ObservationClient.lua
    pain: float = 0.0
    stitch: bool = False
    burn: bool = False
    fracture: bool = False
    glass: bool = False
    splinted: bool = False
    bullet: bool = False
    infection: float = 0.0

class Body(LogExtraFieldsBase):
    health: float = 100.0
    temperature: float = 37.0
    parts: Dict[str, BodyPart] = Field(default_factory=dict)

class InventoryItem(LogExtraFieldsBase):
    id: int
    type: str
    cat: str
    name: str
    weight: float
    cond: float

class Inventory(LogExtraFieldsBase):
    held: Dict[str, Any] = Field(default_factory=dict)
    worn: List[InventoryItem] = Field(default_factory=list)
    main: List[InventoryItem] = Field(default_factory=list)

    @field_validator('worn', 'main', mode='before')
    @classmethod
    def allow_empty_dict_as_list(cls, v):
        if isinstance(v, dict) and not v:
            return []
        if isinstance(v, dict):
             # If it's a dict but not empty, maybe it's a map of id->item?
             # For now, let's treat values as list items
            return list(v.values())
        return v

class Tile(LogExtraFieldsBase):
    x: int
    y: int
    z: int
    room: Optional[str] = None

class WorldObject(LogExtraFieldsBase):
    id: str
    type: str
    x: int
    y: int
    z: int
    meta: Dict[str, Any] = Field(default_factory=dict)

class Neighbor(LogExtraFieldsBase):
    x: int
    y: int
    status: str
    objects: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator('objects', mode='before')
    @classmethod
    def allow_empty_dict_as_list(cls, v):
        if isinstance(v, dict) and not v:
            return []
        if isinstance(v, dict):
             # If it's a dict but not empty, maybe it's a map?
             # Treat values as list items
            return list(v.values())
        return v

class Vision(LogExtraFieldsBase):
    scan_radius: int = 0
    timestamp: int = 0
    tiles: List[Tile] = Field(default_factory=list)
    objects: List[WorldObject] = Field(default_factory=list)
    neighbors: Dict[str, Neighbor] = Field(default_factory=dict)
    debug_z: Optional[Dict[str, Any]] = None

    @field_validator('tiles', 'objects', mode='before')
    @classmethod
    def allow_empty_dict_as_list(cls, v):
        if isinstance(v, dict) and not v:
            return []
        if isinstance(v, dict):
            return list(v.values())
        return v

class ActionState(LogExtraFieldsBase):
    status: str = "idle"
    sequence_number: int = -1
    queue_busy: bool = False
    current_action_id: Optional[str] = None
    current_action_type: Optional[str] = None

class Player(LogExtraFieldsBase):
    status: str
    # vitals: Vitals # Removed
    position: Position
    state: PlayerStateFlags
    rotation: float
    body: Body
    moodles: Dict[str, Any] = Field(default_factory=dict)
    inventory: Inventory
    vision: Vision = Field(default_factory=Vision)
    action_state: ActionState = Field(default_factory=ActionState)

class GameState(LogExtraFieldsBase):
    timestamp: int
    tick: float
    player: Player
