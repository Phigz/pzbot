import logging
import time
from typing import Dict, List, Any, Optional

from .memory_objects import EntityMemory, ContainerMemory, VehicleMemory, GlobalFloorMemory
from ..types import EntityData

import threading

logger = logging.getLogger(__name__)

class MemorySystem:
    def __init__(self):
        self._lock = threading.RLock()
        self.entities: Dict[str, EntityMemory] = {}     # Zombies, Players, Animals
        self.containers: Dict[str, ContainerMemory] = {} # Static containers
        self.vehicles: Dict[str, VehicleMemory] = {}     # Vehicles
        self.world_items: Dict[str, EntityMemory] = {}   # Unused now, but kept for compatibility
        self.signals: List[Dict] = []                   # Radio/TV Signals (Transient)
        self.sounds: List[Dict] = []                    # World Sounds (Transient)

    def update(self, vision: Any):
        """
        Process vision data from game state.
        vision: Expects the Vision object from state.py
        """
        if not vision: return
        
        with self._lock:
            # 1. Dynamic Entities (Zombies)
            objects = getattr(vision, 'objects', []) or []
            self._process_list(objects, self.entities, EntityMemory, "Object")
            
            # Prepare Global Floor Items list
            flat_items = []
            
            # 2. Containers (Extract Floor items)
            containers = getattr(vision, 'nearby_containers', []) or []
            regular_cons = []
            
            for c in containers:
                # Handle Pydantic or Dict for safer access
                # Pydantic V2 prefers model_dump
                if hasattr(c, 'model_dump'):
                    c_data = c.model_dump()
                elif hasattr(c, 'dict'):
                    c_data = c.dict()
                else:
                    c_data = c

                otype = c_data.get('object_type')
                
                if otype == 'Floor':
                    # Extract items for Global Floor Memory
                    c_items = c_data.get('items', [])
                    # Use container position as fallback (usually player pos)
                    cx, cy = c_data.get('x', 0), c_data.get('y', 0)
                    
                    for i in c_items:
                        # Ensure item has coordinates
                        if 'x' not in i: i['x'] = cx
                        if 'y' not in i: i['y'] = cy
                        flat_items.append(i)
                else:
                    regular_cons.append(c)
            
            self._process_list(regular_cons, self.containers, ContainerMemory, "Container")

            # 3. World Items (Direct scan)
            raw_items = getattr(vision, 'world_items', []) or []
            
            if raw_items:
                 logger.debug(f"MemorySystem received {len(raw_items)} world items")

            for item in raw_items:
                d = item.dict() if hasattr(item, 'dict') else (item.model_dump() if hasattr(item, 'model_dump') else item)
                flat_items.append(d)

            if flat_items:
                floor_update = {
                    'id': 'Global_Floor',
                    'type': 'Container',
                    'object_type': 'Floor',
                    'x': 0, 'y': 0, 'z': 0,
                    'properties': {'items': flat_items}
                }
                # Process strictly as GlobalFloorMemory
                self._process_list([floor_update], self.containers, GlobalFloorMemory, "Container")

            # 4. Vehicles
            vehicles = getattr(vision, 'vehicles', []) or []
            self._process_list(vehicles, self.vehicles, VehicleMemory, "Vehicle")

            # 5. Signals (Persistent)
            # Merge new signals with existing memory
            raw_signals = getattr(vision, 'signals', []) or []
            current_time = int(time.time() * 1000)
            
            # Create map of existing signals for easy lookup (by name/channel)
            sig_map = {f"{s['name']}_{s['channel']}": s for s in self.signals}
            
            for s in raw_signals:
                d = s.model_dump() if hasattr(s, 'model_dump') else (s.dict() if hasattr(s, 'dict') else s)
                
                # Add metadata for persistence
                d['last_seen'] = current_time
                d['ttl_remaining_ms'] = 30000 # 30s memory for radio messages
                
                # Deduplicate: Overwrite existing
                key = f"{d['name']}_{d['channel']}"
                sig_map[key] = d
                
            self.signals = list(sig_map.values())

            # 6. Sounds (Transient)
            raw_sounds = getattr(vision, 'sounds', []) or []
            self.sounds = []
            for s in raw_sounds:
                d = s.model_dump() if hasattr(s, 'model_dump') else (s.dict() if hasattr(s, 'dict') else s)
                self.sounds.append(d)

    def _process_list(self, input_list: List[Any], target_dict: Dict, memory_cls, default_type: str):
        if not input_list: return
        
        for item in input_list:
            # Formatting data for storage
            if hasattr(item, 'model_dump'):
                data = item.model_dump()
            elif hasattr(item, 'dict'):
                data = item.dict()
            else:
                data = item # Assume dict
            
            # Extract ID
            obj_id = data.get('id')
            
            # Type fallback
            if 'type' not in data or not data['type']:
                data['type'] = default_type

            # Filter out Dynamic Containers (e.g. Equipped Bags) from Static Memory
            # We only want to persist World/Object containers.
            # Entities (like Player) move, so we shouldn't create static map dots for them.
            if default_type == "Container":
                meta = data.get('meta', {})
                if meta.get('parent_type') == 'Entity':
                    continue

            # Container ID generation fix (same as old EntityManager)
            if not obj_id and data.get('type') == 'Container':
                 x = data.get('x', 0)
                 y = data.get('y', 0)
                 z = data.get('z', 0)
                 obj_id = f"container_{x}_{y}_{z}"
                 data['id'] = obj_id

            if not obj_id: continue

            wrapped_data = self._wrap_data(data)
            
            # Update or Create
            if obj_id in target_dict:
                target_dict[obj_id].update(wrapped_data)
            else:
                target_dict[obj_id] = memory_cls(obj_id, wrapped_data)

    def _wrap_data(self, data: dict):
        # Maps raw input dict to EntityData structure
        meta = data.get('meta', {})
        # Merge unknowns into meta/properties
        props = data.get('properties', {}) or {}
        if meta: props.update(meta)
        
        # Handle special fields that might be top-level in input but need to be in properties for EntityData
        if 'items' in data: props['items'] = data['items']
        if 'parts' in data: props['parts'] = data['parts']
        if 'object_type' in data: props['object_type'] = data['object_type']
        
        # For WorldItem
        if 'name' in data: props['name'] = data['name']
        if 'category' in data: props['category'] = data['category']
        if 'count' in data: props['count'] = data['count']

        return EntityData(
            id=str(data.get('id')),
            type=data.get('type', 'Unknown'),
            x=float(data.get('x', 0)),
            y=float(data.get('y', 0)),
            z=float(data.get('z', 0)),
            properties=props
        )

    def decay(self):
        current_time = int(time.time() * 1000)
        
        with self._lock:
            self._decay_collection(self.entities, current_time)
            self._decay_collection(self.containers, current_time)
            self._decay_collection(self.vehicles, current_time)
            self._decay_collection(self.world_items, current_time)
            
            # Decay Signals (List of Dicts)
            fresh_signals = []
            for s in self.signals:
                expiration = s.get('last_seen', 0) + s.get('ttl_remaining_ms', 0)
                # Recalculate remaining TTL based on current time
                remaining = expiration - current_time
                if remaining > 0:
                    s['ttl_remaining_ms'] = remaining
                    fresh_signals.append(s)
            self.signals = fresh_signals

    def _decay_collection(self, collection: Dict, current_time: int):
        to_remove = []
        for eid, mem_obj in collection.items():
            if not mem_obj.decay(current_time):
                to_remove.append(eid)
        
        for eid in to_remove:
            del collection[eid]

    # Getters for Snapshot/Debug
    # Getters for Snapshot/Debug
    def get_entities(self):
        with self._lock:
            return [m.as_dict() for m in self.entities.values()]
    
    def get_known_containers(self):
        with self._lock:
            return [m.as_dict() for m in self.containers.values()]
        
    def get_known_items(self):
        with self._lock:
            return [m.as_dict() for m in self.world_items.values()]

    def get_known_vehicles(self):
        with self._lock:
            return [m.as_dict() for m in self.vehicles.values()]

    def get_signals(self):
        with self._lock:
            # Signals are now stored as dicts with TTL, return list
            return self.signals

    def get_sounds(self):
        with self._lock:
            return self.sounds

