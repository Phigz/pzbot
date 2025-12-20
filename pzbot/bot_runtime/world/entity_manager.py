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

    def process_vision(self, visible_objects: List[Any], world_items: List[Any] = None, containers: List[Any] = None):
        """
        Updates entities based on current vision.
        Marks missing entities as not visible based on TTL.
        """
        current_time = int(time.time() * 1000)
        current_ids = set()
        
        # Helper to process lists
        def process_list(obj_list, default_type="Unknown"):
            if not obj_list: return
            for obj in obj_list:
                # Handle Pydantic models vs dicts vs Objects
                eid = getattr(obj, 'id', None)
                if not eid and isinstance(obj, dict): eid = obj.get('id')
                
                # Container ID generation (if missing)
                if not eid and (getattr(obj, 'type', '') == 'Container' or (isinstance(obj, dict) and obj.get('type') == 'Container')):
                     # Containers from Sensor often lack stable IDs unless we generate them from coords
                     # Using x_y_z as stable ID for static containers
                     x = getattr(obj, 'x', 0) if hasattr(obj, 'x') else obj.get('x', 0)
                     y = getattr(obj, 'y', 0) if hasattr(obj, 'y') else obj.get('y', 0)
                     z = getattr(obj, 'z', 0) if hasattr(obj, 'z') else obj.get('z', 0)
                     eid = f"container_{x}_{y}_{z}"
                
                if not eid: continue
                current_ids.add(eid)
                
                # Extract properties
                meta = getattr(obj, 'meta', {})
                if isinstance(obj, dict): meta = obj.get('meta', {}) or {}
                
                # Ensure object_type is preserved in meta
                obj_type = getattr(obj, 'object_type', None)
                if isinstance(obj, dict): obj_type = obj.get('object_type')
                if obj_type:
                    meta['object_type'] = obj_type
                
                # Special handling for Container items
                items = getattr(obj, 'items', None)
                if isinstance(obj, dict): items = obj.get('items')
                if items is not None:
                     # Convert Pydantic models to dicts for serialization
                     serialized_items = []
                     for i in items:
                         if hasattr(i, 'model_dump'):
                             serialized_items.append(i.model_dump())
                         elif hasattr(i, 'dict'):
                             serialized_items.append(i.dict())
                         else:
                             serialized_items.append(i)
                     meta['items'] = serialized_items

                etype = getattr(obj, 'type', default_type)
                if isinstance(obj, dict): etype = obj.get('type', default_type)
                
                # Handle coords
                x = getattr(obj, 'x', 0) if hasattr(obj, 'x') else obj.get('x', 0)
                y = getattr(obj, 'y', 0) if hasattr(obj, 'y') else obj.get('y', 0)
                z = getattr(obj, 'z', 0) if hasattr(obj, 'z') else obj.get('z', 0)

                self.update_entity(eid, etype, x, y, z, meta)

        # 1. Process all inputs
        process_list(visible_objects, "Object")
        process_list(world_items, "WorldItem")
        process_list(containers, "Container")

        # 2. Process Ghosts (Decay)
        to_remove = []
        for eid, ent in self.entities.items():
            if eid not in current_ids:
                # Mark as Ghost
                ent.is_visible = False
                
                # Check Decay based on Type
                age = current_time - ent.last_seen
                ttl = settings.MEMORY_TTL_STATIC # Default 60s
                
                if ent.type in ['Zombie', 'Player']:
                    ttl = settings.MEMORY_TTL_ZOMBIE # Short (10s)
                elif ent.type == 'Container':
                    ttl = 3600 * 1000 * 24 # Stay for 24 hours (effectively infinite for session)
                elif ent.type == 'WorldItem':
                    ttl = 600 * 1000 # 10 minutes
                    
                if age > ttl:
                    to_remove.append(eid)
        
        # 3. Cleanup
        for eid in to_remove:
            del self.entities[eid]
            
    def get_known_containers(self) -> List[EntityData]:
        return [e for e in self.entities.values() if e.type == 'Container']

    def get_known_items(self) -> List[EntityData]:
        return [e for e in self.entities.values() if e.type == 'WorldItem']
