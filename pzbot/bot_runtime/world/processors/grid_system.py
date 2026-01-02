import os
import json
import time
import logging
import threading
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from pydantic import BaseModel

from ..types import TileData, GridChunkData
from .memory_objects import GridChunkMemory

logger = logging.getLogger(__name__)

CHUNK_SIZE = 10

class GridSystem:
    """
    Manages the spatial grid using 10x10 Chunks.
    Handles persistence to disk to control memory usage.
    """
    def __init__(self, base_dir: Path):
        self.data_dir = base_dir / "data" / "chunks"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.chunks: Dict[Tuple[int, int], GridChunkMemory] = {}
        self._lock = threading.RLock()
        
        # Bounds of currently loaded area
        self.min_x = 0
        self.max_x = 0
        self.min_y = 0
        self.max_y = 0

    def update(self, visible_tiles: List[Any], timestamp: int):
        if not visible_tiles: return
        
        chunk_updates: Dict[Tuple[int, int], List[Any]] = {}
        
        for t in visible_tiles:
            if hasattr(t, 'dict'): t_data = t.dict()
            else: t_data = t
            x, y = t_data['x'], t_data['y']
            
            # Update bounds
            self.min_x = min(self.min_x, x)
            self.max_x = max(self.max_x, x)
            self.min_y = min(self.min_y, y)
            self.max_y = max(self.max_y, y)

            cx = x // CHUNK_SIZE
            cy = y // CHUNK_SIZE
            key = (cx, cy)
            
            if key not in chunk_updates:
                chunk_updates[key] = []
            chunk_updates[key].append(t_data)

        with self._lock:
            for key, tiles in chunk_updates.items():
                chunk = self._get_or_load_chunk(key[0], key[1])
                for t_data in tiles:
                    tile_key = f"{t_data['x']}_{t_data['y']}_{t_data.get('z',0)}"
                    chunk.data.tiles[tile_key] = TileData(**t_data)
                chunk.last_seen = timestamp
                chunk.is_dirty = True

    def _get_or_load_chunk(self, cx: int, cy: int) -> GridChunkMemory:
        # Assumes Lock is held by caller
        key = (cx, cy)
        if key in self.chunks:
            return self.chunks[key]
        
        chunk_file = self.data_dir / f"chunk_{cx}_{cy}.json"
        if chunk_file.exists():
            try:
                with open(chunk_file, 'r') as f:
                    data = json.load(f)
                    chunk_data = GridChunkData(**data)
                    memory = GridChunkMemory(f"chunk_{cx}_{cy}", chunk_data)
                    self.chunks[key] = memory
                    return memory
            except Exception as e:
                logger.error(f"Failed to load chunk {cx},{cy}: {e}")
        
        new_data = GridChunkData(chunk_x=cx, chunk_y=cy)
        memory = GridChunkMemory(f"chunk_{cx}_{cy}", new_data)
        self.chunks[key] = memory
        return memory

    def save_snapshot(self, path: str, additional_data: Dict[str, Any] = None):
        with self._lock:
            # 1. Update Dirty Chunks to Disk
            for key, chunk in self.chunks.items():
                if chunk.is_dirty:
                    self._save_chunk_to_disk(chunk)

            # 2. Generate flat snapshot
            all_tiles = []
            min_x, max_x, min_y, max_y = 999999, -999999, 999999, -999999
            has_data = False

            for chunk in self.chunks.values():
                for t in chunk.data.tiles.values():
                    all_tiles.append(t.dict())
                    min_x = min(min_x, t.x)
                    max_x = max(max_x, t.x)
                    min_y = min(min_y, t.y)
                    max_y = max(max_y, t.y)
                    has_data = True
            
        snapshot = {
            "timestamp": time.time(),
            "tiles": all_tiles,
            "bounds": {
                "min_x": min_x if has_data else 0,
                "max_x": max_x if has_data else 0,
                "min_y": min_y if has_data else 0,
                "max_y": max_y if has_data else 0
            }
        }
        
        if additional_data:
            snapshot.update(additional_data)
            
        temp_path = path + ".tmp"
        
        # Retry mechanism for file locking (WinError 32)
        max_retries = 3
        saved = False
        
        for attempt in range(max_retries):
            try:
                with open(temp_path, 'w') as f:
                    json.dump(snapshot, f)
                
                if os.path.exists(path):
                    os.remove(path)
                os.replace(temp_path, path)
                saved = True
                break
            except OSError as e:
                # Wait and retry if file is locked
                if attempt < max_retries - 1:
                    time.sleep(0.1)
                    continue
                logger.error(f"Failed to save snapshot (OS Error): {e}")
            except Exception as e:
                logger.error(f"Failed to save snapshot: {e}")
                break

        if saved:
            ent_count = len(snapshot.get('entities', []))
            sig_count = len(snapshot.get('signals', []))
            logger.info(f"Saved snapshot with {len(all_tiles)} tiles, {ent_count} entities, {sig_count} signals")

    def _save_chunk_to_disk(self, chunk: GridChunkMemory):
        path = self.data_dir / f"chunk_{chunk.data.chunk_x}_{chunk.data.chunk_y}.json"
        try:
            with open(path, 'w') as f:
                f.write(chunk.data.model_dump_json())
            chunk.is_dirty = False
        except Exception as e:
            logger.error(f"Failed to save chunk disk: {e}")

    def maintenance(self):
        now = int(time.time() * 1000)
        keys_to_remove = []
        
        with self._lock:
            for key, chunk in self.chunks.items():
                age = now - chunk.last_seen
                if age > chunk.get_ttl():
                    if chunk.is_dirty:
                        self._save_chunk_to_disk(chunk)
                    keys_to_remove.append(key)
            
            for k in keys_to_remove:
                del self.chunks[k]

    def get_stats(self) -> Dict[str, int]:
        total_tiles = sum(len(c.data.tiles) for c in self.chunks.values())
        return {
            "total_tiles": total_tiles,
            "loaded_chunks": len(self.chunks)
        }

    def get_tile(self, x: int, y: int, z: int) -> Optional[Any]:
        cx = int(x) // CHUNK_SIZE
        cy = int(y) // CHUNK_SIZE
        key = (cx, cy)
        
        with self._lock:
            if key in self.chunks:
                tile_key = f"{int(x)}_{int(y)}_{int(z)}"
                return self.chunks[key].data.tiles.get(tile_key)
        return None
