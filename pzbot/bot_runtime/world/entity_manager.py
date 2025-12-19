import logging
import time
from typing import Dict, List, Optional, Any
from .types import EntityData
from ..config import settings

logger = logging.getLogger(__name__)

class EntityManager:
    """
    Tracks dynamic entities (Zombies, Players, Items) over time.
    Handles ID matching and position updates.
    """
    def __init__(self):
        self.entities: Dict[str, EntityData] = {}

    def update_entity(self, entity_id: str, ent_type: str, x: float, y: float, z: float, meta: dict = None):
        """Updates or adds an entity."""
        if entity_id not in self.entities:
            self.entities[entity_id] = EntityData(
                id=entity_id,
                type=ent_type,
                x=x,
                y=y,
                z=z,
                properties=meta or {}
            )
        else:
            ent = self.entities[entity_id]
            ent.x = x
            ent.y = y
            ent.z = z
            ent.last_seen = int(time.time() * 1000)
            ent.is_visible = True
            if meta:
                ent.properties.update(meta)

    def process_vision(self, visible_objects: List[Any]):
        """
        Updates entities based on current vision.
        Marks missing entities as not visible based on TTL.
        """
        current_time = int(time.time() * 1000)
        
        current_ids = set()
        
        # 1. Update Visible Entities
        for obj in visible_objects:
            eid = obj.id
            if not eid:
                continue
                
            current_ids.add(eid)
            self.update_entity(
                entity_id=eid,
                ent_type=obj.type or "Unknown",
                x=obj.x,
                y=obj.y,
                z=obj.z,
                meta=obj.meta
            )
            
        # 2. Process Ghosts (Decay)
        to_remove = []
        for eid, ent in self.entities.items():
            if eid not in current_ids:
                # Mark as Ghost
                ent.is_visible = False
                
                # Check Decay (Use Config)
                age = current_time - ent.last_seen
                ttl = settings.MEMORY_TTL_STATIC
                if ent.type == 'Zombie' or ent.type == 'Player':
                    ttl = settings.MEMORY_TTL_ZOMBIE
                    
                if age > ttl:
                    to_remove.append(eid)
        
        # 3. Cleanup
        for eid in to_remove:
            del self.entities[eid]
