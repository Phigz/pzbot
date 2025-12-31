import time
import logging
from typing import Dict, Any, Optional
from ..types import EntityData, TileData, GridChunkData
from ...config import settings

logger = logging.getLogger(__name__)

class MemoryObject:
    """
    Base class for any persisted object in memory.
    Handles decay, confidence, and validity checks.
    """
    def __init__(self, obj_id: str, data: Any):
        self.id = obj_id
        self.data = data
        self.last_seen = int(time.time() * 1000)
        self.confidence = 1.0  # 1.0 = absolute certainty (live), 0.0 = forgotten
        
    def update(self, data: Any):
        """Refreshes the object with new data."""
        self.data = data
        self.last_seen = int(time.time() * 1000)
        self.confidence = 1.0

    def decay(self, current_time: int) -> bool:
        """
        Calculates confidence loss. Returns False if object should be removed (confidence <= 0).
        Base implementation uses strict TTL.
        """
        age = current_time - self.last_seen
        # Default simple TTL check if no linear decay configured
        if age > self.get_ttl():
            self.confidence = 0.0
            return False
            
        # Optional: Linear decay for UI visualization / heuristics
        # self.confidence = max(0.0, 1.0 - (age / self.get_ttl()))
        return True

    def get_ttl(self) -> int:
        return 60 * 1000 # Default 60s

    def as_dict(self):
        d = self.data.dict() if hasattr(self.data, 'dict') else self.data
        if isinstance(d, dict):
            # Calculate remaining TTL
            ttl = self.get_ttl()
            elapsed = int(time.time() * 1000) - self.last_seen
            d['ttl_remaining_ms'] = max(0, ttl - elapsed)
        return d

class EntityMemory(MemoryObject):
    """
    Dynamic entities: Zombies, Players, Animals.
    Fast decay.
    """
    def get_ttl(self) -> int:
        # Variable TTL based on Entity Type
        # Handle dict or Pydantic model
        if isinstance(self.data, dict):
            dtype = self.data.get('type')
        else:
            dtype = getattr(self.data, 'type', None)

        if dtype == 'Player':
            return 30 * 1000 # 30s for Players (High Value)
        elif dtype == 'Animal':
            return 20 * 1000 # 20s for Animals
            
        # Default (Zombies)
        return settings.MEMORY_TTL_ZOMBIE

    def decay(self, current_time: int) -> bool:
        # Linear confidence drop for moving targets
        age = current_time - self.last_seen
        ttl = self.get_ttl()
        if age > ttl: return False
        
        self.confidence = 1.0 - (age / ttl)
        return True

class ContainerMemory(MemoryObject):
    """
    Static Loot Containers.
    Very long decay (Session).
    """
    def update(self, data: Any):
        # Merge logic: Don't overwrite known items with "empty" scan if we just didn't see inside?
        # For now, simplistic overwrite, assuming 'data' comes from a valid inspection.
        # Ideally, we only update if we actively 'inspected' it.
        super().update(data)

    def get_ttl(self) -> int:
        # Static containers
        return settings.MEMORY_TTL_CONTAINER

class VehicleMemory(MemoryObject):
    """
    Vehicles.
    Medium decay.
    """
    def get_ttl(self) -> int:
        return settings.MEMORY_TTL_VEHICLE 

    def decay(self, current_time: int) -> bool:
        age = current_time - self.last_seen
        ttl = self.get_ttl()
        if age > ttl: return False
        
        # Slow confidence drop
        self.confidence = max(0.2, 1.0 - (age / ttl)) # Never fully forget a car unless VERY old?
        if age > ttl: return False
        return True

class GridChunkMemory(MemoryObject):
    """
    Map Chunks (10x10 Tiles).
    Persisted to disk, managed by RAM cache.
    """
    def __init__(self, chunk_id: str, data: GridChunkData):
        super().__init__(chunk_id, data)
        self.is_dirty = False # Needs save to disk

    def update(self, data: GridChunkData):
        self.data = data
        self.last_seen = int(time.time() * 1000)
        self.is_dirty = True

    def get_ttl(self) -> int:
        # RAM Cache TTL. If not visited for 5 minutes, unload (save if dirty).
        return 300 * 1000

class GlobalFloorMemory(MemoryObject):
    """
    Special memory object for the "Floor" container.
    Aggregates items from all visited floor tiles into a single container.
    Items have individual decay times.
    """
    def __init__(self, obj_id: str, data: Any):
        super().__init__(obj_id, data)
        self.item_map = {} # ItemID -> {data: dict, last_seen: int}
        self.update(data)
        
    def update(self, data: Any):
        # Data is a specific Floor tile (Container)
        # Extract items and merge them
        if hasattr(data, 'model_dump'):
            d = data.model_dump()
        elif hasattr(data, 'dict'):
            d = data.dict()
        else:
            d = data

        props = d.get('properties', {})
        items = props.get('items', [])
        
        current_time = int(time.time() * 1000)
        
        # Tile coordinates
        tx, ty = d.get('x'), d.get('y')
        
        # Debug Logging for Duplication
        if items:
             logger.debug(f"GlobalFloor Update: Tile({tx},{ty}) Items: {len(items)}")

        for item in items:
            i_data = item.copy()
            # Stamp location if not present (inherited from tile)
            if 'x' not in i_data: i_data['x'] = tx
            if 'y' not in i_data: i_data['y'] = ty
            
            # Use Item ID as key. If missing, generate based on tile to avoid float jitter duplicates
            # Sensor logic ensures IDs for most things.
            raw_id = i_data.get('id')
            if raw_id:
                iid = str(raw_id)
            else:
                # Fallback: Use type and INTEGER coordinates
                # This groups items of same type on same tile if they lack IDs
                idx, idy = int(tx), int(ty)
                iid = f"unknown_{idx}_{idy}_{i_data.get('type', 'Item')}"
            
            # Persist the ID so visualization sees it
            i_data['id'] = iid
            
            self.item_map[iid] = {
                'data': i_data,
                'last_seen': current_time
            }
            
        # Update main container stats
        self.last_seen = current_time
        
    def decay(self, current_time: int) -> bool:
        # Decay internal items
        ttl = self.get_ttl()
        to_remove = []
        for iid, info in self.item_map.items():
            age = current_time - info['last_seen']
            if age > ttl:
                to_remove.append(iid)
                
        for iid in to_remove:
            del self.item_map[iid]
            
        return True # Always alive
        
    def as_dict(self):
        # Return as a Container
        parent_id = "Floor" # Or generic
        
        current_time = int(time.time() * 1000)
        ttl = self.get_ttl()
        
        items_export = []
        for info in self.item_map.values():
            d = info['data'].copy()
            elapsed = current_time - info['last_seen']
            d['ttl_remaining_ms'] = max(0, ttl - elapsed)
            items_export.append(d)
        

            
        return {
            'id': self.id,
            'type': 'Container',
            'x': 0, 'y': 0, 'z': 0,
            'object_type': 'Floor', # Display name
            'ttl_remaining_ms': 31536000000, # 1 Year (Hidden in UI)
            'meta': {'parent_id': parent_id},
            'items': items_export,
            'properties': { # Legacy support
                'items': items_export
            }
        }
        
    def get_ttl(self) -> int:
        return settings.MEMORY_TTL_ITEM
