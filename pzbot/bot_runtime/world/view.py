from typing import List, Protocol, Optional, Callable, Any, runtime_checkable
from .types import EntityData
from bot_runtime.ingest.state import Player

EntityType = str

@runtime_checkable
class WorldView(Protocol):
    """
    A read-only interface for reasoning layers to access world data.
    Decouples the internal WorldModel implementation from consumers.
    """
    
    @property
    def player(self) -> Optional[Player]:
        """Returns the current player state."""
        ...

    def get_entities(self, type_filter: Optional[str] = None) -> List[EntityData]:
        """
        Returns a list of tracked entities, optionally filtered by type.
        """
        ...
        
    def find_nearest_entity(self, x: float, y: float, type_filter: Optional[str] = None) -> Optional[EntityData]:
        """
        Finds the nearest entity to the given coordinates.
        """
        ...
    
    def get_vision_age(self) -> float:
        """
        Returns time in seconds since the last valid vision update.
        Useful for determining if the world model is stale.
        """
        ...
