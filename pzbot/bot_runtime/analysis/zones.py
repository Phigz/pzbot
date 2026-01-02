import yaml
import logging
from typing import Dict, List, Optional
from collections import Counter

from bot_runtime import config as bot_config
from bot_runtime.analysis.base import BaseAnalyzer
from bot_runtime.brain.state import BrainState, CharacterPersonality, ZoneState
from bot_runtime.world.model import WorldModel

logger = logging.getLogger(__name__)

class ZoneAnalyzer(BaseAnalyzer):
    """
    Determines the semantic 'Zone' the bot is currently in.
    Reads 'room' data from perceived tiles and maps them to Tags using 'config/zones.yaml'.
    
    Output: state.zone (ZoneState)
    """

    def __init__(self, personality: CharacterPersonality):
        super().__init__(personality)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        path = bot_config.BASE_DIR / "config" / "zones.yaml"
        if not path.exists():
            return {"mappings": {}}
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {"mappings": {}}
        except Exception as e:
            logger.error(f"Failed to load zones.yaml: {e}")
            return {"mappings": {}}

    def analyze(self, memory: WorldModel, needs=None) -> ZoneState:
        # 1. Identify Current Room Name
        # Heuristic: Check the tile under the player, or the majority of nearby tiles.
        # Vision tiles contain 'room' field if Sensor.lua provides it.
        
        # We assume the memory snapshot passed in is the latest *processed* snapshot.
        # Ideally we look at 'memory.player.position' and finding valid tile data.
        # But 'WorldModel' abstracts this. Let's look at the raw vision data from the latest input if possible,
        # or rely on what we stored. 
        # Actually, BaseAnalyzer.analyze typically takes 'memory' (WorldModel).
        # We need to access the latest 'grid' or 'vision' data.
        # In current architecture, 'memory' contains persistent data.
        # The 'Brain' passes 'state.world' usually? 
        # Wait, 'analyze' signature in 'brain.py' passes (self.memory, self.state.needs).
        # We might need to access the 'raw snapshot' for real-time room data, 
        # as WorldModel focuses on persistent Tiles.
        
        # Let's assume WorldModel.get_tile(x, y) returns a Tile object with 'room' attribute.
        # (We need to ensure Tile model has 'room')
        
        player = memory.player
        if not player:
            return ZoneState(current_zone="Unknown", tags=[])

        px, py = int(player.position.x), int(player.position.y)
        
        # Check current tile
        # Note: We rely on the GridSystem having updated the tiles with room data.
        current_room = "Outdoors"
        
        # We can scan a small radius to handle "Standing in a doorway" edge cases
        room_names = []
        
        # Check 3x3
        for dh in [-1, 0, 1]:
            for dw in [-1, 0, 1]:
                 tile = memory.get_tile(px + dw, py + dh)
                 if tile and tile.room:
                     room_names.append(tile.room)

        if room_names:
            # Pick most common room name (ignoring 'hall' maybe? No, hall is valid)
            counts = Counter(room_names)
            current_room = counts.most_common(1)[0][0]
        
        # 2. Map Room Name to Semantic Tags
        tags = self._resolve_tags(current_room)
        
        # 3. Construct ZoneState
        z_state = ZoneState(
            current_zone=current_room,
            tags=tags,
            last_update_tick=0 # TODO: Pass clock?
        )
        
        return z_state

    def _resolve_tags(self, room_name: str) -> List[str]:
        if not room_name or room_name == "Outdoors":
            return ["Outdoors"]
            
        name_lower = room_name.lower()
        mappings = self.config.get('mappings', {})
        
        found_tags = set()
        
        # Exact/Partial Keys
        for key, t_list in mappings.items():
            if key in name_lower:
                for t in t_list:
                    found_tags.add(t)
                    
        # Heuristics based on name construction if no mapping found
        if not found_tags:
            if "storage" in name_lower: found_tags.add("Storage")
            if "bed" in name_lower: found_tags.add("Comfort")
            
        return list(found_tags)
