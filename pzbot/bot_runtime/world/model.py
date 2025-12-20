import logging
import time
from typing import Optional
from bot_runtime.ingest.state import GameState, Player, Vision, ZombieState
from .entity_manager import EntityManager
from bot_runtime.world.grid import SpatialGrid
from bot_runtime.world.view import WorldView, EntityType
from .types import EntityData

logger = logging.getLogger(__name__)

class WorldModel(WorldView):
    """
    The central brain of the bot's understanding of the world.
    Aggregates momentary `GameState` snapshots into a persistent map and entity list.
    """
    def __init__(self):
        self.current_state: Optional[GameState] = None
        self.tick_count = 0
        self.last_update_time = 0.0
        
        # Persistent Sub-systems
        self.entities = EntityManager()
        self.grid = SpatialGrid()

    def update(self, new_state: GameState):
        """Updates the world model with a new game state."""
        self.current_state = new_state
        self.tick_count += 1
        self.last_update_time = time.time()
        
        # 1. Update Map with new vision data
        if new_state.player and new_state.player.vision:
            vision = new_state.player.vision
            
            # Use the new consolidated Grid
            if vision.tiles:
                self.grid.update(vision.tiles)
                
            # Update Entities
            self.entities.process_vision(
                visible_objects=vision.objects,
                world_items=vision.world_items, # New: Persistent Items
                containers=vision.nearby_containers # New: Persistent Containers
            )

            
    @property
    def player(self) -> Optional[Player]:
        return self.current_state.player if self.current_state else None

    @property
    def vision(self) -> Optional[Vision]:
        return self.current_state.vision if self.current_state else None

    # --- WorldView Implementation ---

    def get_entities(self, type_filter: Optional[str] = None) -> list[EntityData]:
        """Returns a list of tracked entities."""
        all_entities = list(self.entities.entities.values())
        if type_filter:
            return [e for e in all_entities if e.type == type_filter]
        return all_entities

    def find_nearest_entity(self, x: float, y: float, type_filter: Optional[str] = None) -> Optional[EntityData]:
        """Finds nearest entity."""
        schema = self.get_entities(type_filter)
        if not schema:
            return None
        
        nearest = None
        min_dist_sq = float('inf')
        
        for ent in schema:
            dist_sq = (ent.x - x)**2 + (ent.y - y)**2
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                nearest = ent
                
        return nearest

    def get_vision_age(self) -> float:
        """Returns seconds since last update."""
        if not self.current_state or self.last_update_time == 0.0:
            return float('inf')
        
        return time.time() - self.last_update_time
