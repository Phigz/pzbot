import logging
from typing import Dict, List, Any, Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

class LogExtraFieldsBase(BaseModel):
    class Config:
        extra = 'ignore' # Ignore fields we don't know about yet (but ideally we log them)
        populate_by_name = True

    @classmethod
    def check_for_extra_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Check for keys in data that are not in the model fields
            # We need to handle aliases if they exist
            
            allowed_keys = set()
            for name, field in cls.model_fields.items():
                allowed_keys.add(name)
                if field.alias:
                    allowed_keys.add(field.alias)

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
    at_window: bool = False
    read_book: bool = False
    is_driving: bool = False

class PlayerBody(LogExtraFieldsBase):
    health: float = 0.0
    stamina: float = 0.0
    hunger: float = 0.0
    thirst: float = 0.0
    stress: float = 0.0
    fatigue: float = 0.0
    panic: float = 0.0
    temperature: float = 0.0
    is_infected: bool = False
    is_bitten: bool = False
    is_scratched: bool = False
    is_dead: bool = False

class ActionState(LogExtraFieldsBase):
    status: str = "IDLE"
    current_action: str = ""
    current_action_target: str = ""
    queue_length: int = 0
    
    # New Fields based on mod output
    batch_id: int = 0
    batch_index: int = 0
    queue_busy: bool = False
    current_action_id: Optional[str] = None
    current_action_type: str = "IDLE"

class Player(LogExtraFieldsBase):
    guid: str = "unknown"
    player_num: int = 0
    position: Position
    flags: PlayerStateFlags = Field(default_factory=PlayerStateFlags)
    body: PlayerBody = Field(default_factory=PlayerBody)
    stats: Dict[str, Any] = Field(default_factory=dict)
    vision: Optional['Vision'] = None 
    action_state: ActionState = Field(default_factory=ActionState)
    # New Fields for UI
    moodles: List[Dict[str, Any]] = Field(default_factory=list)
    inventory: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator('moodles', 'inventory', mode='before')
    @classmethod
    def validate_lists(cls, v):
        if isinstance(v, dict) and not v: return []
        if isinstance(v, dict): return list(v.values())
        return v

class Tile(LogExtraFieldsBase):
    x: int
    y: int
    z: int
    w: bool # walkable
    room: Optional[str] = None
    layer: Optional[str] = None

class WorldObject(LogExtraFieldsBase):
    id: str
    type: str # Zombie, Player, Window, Door
    x: int
    y: int
    z: int
    meta: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('meta', mode='before')
    @classmethod
    def allow_empty_dict_as_list(cls, v):
        if isinstance(v, list) and not v:
            return {}
        return v
    
class WorldItem(LogExtraFieldsBase):
    id: str
    type: str
    name: str
    category: str
    x: int
    y: int
    z: int
    count: int = 1

    class Config:
        extra = 'allow'

class ContainerItem(LogExtraFieldsBase):
    id: Optional[str] = None
    type: str
    name: str
    count: int = 1
    category: str = "Unknown"

    class Config:
        extra = 'allow'

class Container(LogExtraFieldsBase):
    type: str = "Container"
    object_type: str = "Unknown"
    x: int
    y: int
    z: int
    items: List[ContainerItem] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('items', mode='before')
    @classmethod
    def allow_empty_dict_as_list(cls, v):
        if isinstance(v, dict) and not v:
            return []
        if isinstance(v, dict):
            return list(v.values())
        return v
    
    @field_validator('meta', mode='before')
    @classmethod
    def allow_empty_dict_as_list_meta(cls, v):
        if isinstance(v, list) and not v:
            return {}
        return v

class Vehicle(LogExtraFieldsBase):
    id: str
    type: str # "Vehicle"
    object_type: str # ScriptName e.g. "Base.Van"
    x: float
    y: float
    z: float
    meta: Dict[str, Any] = Field(default_factory=dict)
    parts: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator('parts', mode='before')
    @classmethod
    def allow_empty_dict_as_list(cls, v):
        if isinstance(v, dict) and not v:
            return []
        if isinstance(v, dict):
            return list(v.values())
        return v

class Signal(LogExtraFieldsBase):
    type: str # "Radio", "TV"
    name: str = "Unknown"
    x: int
    y: int
    z: int
    on: bool = False
    channel: int = -1
    volume: float = 0.0
    msg: Optional[str] = None

class Sound(LogExtraFieldsBase):
    type: str = "Unknown"
    x: int
    y: int
    z: int
    radius: int = 0
    volume: float = 0.0
    source: str = "Unknown"

class Vision(LogExtraFieldsBase):
    scan_radius: int = 0
    timestamp: int = 0
    tiles: List[Tile] = Field(default_factory=list)
    objects: List[WorldObject] = Field(default_factory=list)
    vehicles: List[Vehicle] = Field(default_factory=list)
    world_items: List[WorldItem] = Field(default_factory=list)
    nearby_containers: List[Container] = Field(default_factory=list)
    neighbors: Dict[str, Any] = Field(default_factory=dict)
    
    # New Sensory Channels
    signals: List[Signal] = Field(default_factory=list)
    sounds: List[Sound] = Field(default_factory=list)
    
    debug_z: Optional[Dict[str, Any]] = None

    @field_validator('tiles', 'objects', 'world_items', 'nearby_containers', 'vehicles', 'signals', 'sounds', mode='before')
    @classmethod
    def validate_lists(cls, v, info):
        # Lua output often sends empty dict {} instead of empty list []
        if isinstance(v, dict) and not v:
            return []
        if isinstance(v, dict):
             # Try to convert dict to list (keys usually strings "1", "2" etc.)
             return list(v.values())
        return v

class Environment(LogExtraFieldsBase):
    time_of_day: float = 0.0
    weather: str = ""
    temperature: float = 0.0
    rain_intensity: float = 0.0
    fog_intensity: float = 0.0
    nearby_containers: List[Container] = Field(default_factory=list) # Global containers fallback

    @field_validator('nearby_containers', mode='before')
    @classmethod
    def validate_containers(cls, v):
        if isinstance(v, dict) and not v: return []
        if isinstance(v, dict): return list(v.values())
        return v

class GameState(LogExtraFieldsBase):
    timestamp: float = 0.0
    tick: float = 0.0
    player: Player
    environment: Optional[Environment] = None

    def __init__(self, **data):
        # We need to handle potential serialization quirks from Lua here BEFORE Pydantic
        # Or rely on type adapters.
        super().__init__(**data)
