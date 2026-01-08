import math
import logging
from typing import Optional, Tuple, List

from bot_runtime.brain.state import BrainState

logger = logging.getLogger(__name__)

class GeoAnalyzer:
    """
    Analyzes spatial data to find buildings, entry points, and high-level targets.
    """
    
    @staticmethod
    def get_nearest_building(state: BrainState, exclude_set: set = None) -> Optional[dict]:
        """
        Finds the nearest building centroid that is not in the exclude set.
        Returns a dict with {x, y, id} or None.
        
        NOTE: Since we don't have a global map of buildings yet, 
        we rely on 'Simulation Evidence' or 'Memory'.
        For the prototype, this might return a mock or rely on seeing "Walls" in vision.
        
        Real implementation would parse `map_zones` or `chunk_data` if available.
        For now, we return None if we can't see anything, or a heuristic.
        """
        # Placeholder: If the sensor doesn't provide building lists, 
        # we can't easily "Find nearest building" from scratch without map data.
        # However, we can scan `vision.tiles` for `layer="Wall"`.
        
        # Simple Heuristic: Return center of 'Wall' clusters?
        # Too expensive for python?
        
        # PROTOTYPE HACK:
        # We assume the user creates a 'KnownLocations' list or we rely on vision.
        # If we see a wall, that's a building.
        return None

    @staticmethod
    def get_building_entry(state: BrainState, building_center: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Finds a Door or Window near the target building.
        """
        if not state.vision or not state.vision.objects:
            return None
            
        best = None
        best_dist = 9999
        
        bx, by = building_center
        
        for obj in state.vision.objects:
            if "Door" in obj.type or "Window" in obj.type:
                 dist = math.dist((obj.x, obj.y), (bx, by))
                 # Only consider if it's "part" of that building (close enough)
                 # Hard to say without building extents.
                 if dist < 20: 
                     d2 = math.dist((state.player.position.x, state.player.position.y), (obj.x, obj.y))
                     if d2 < best_dist:
                         best_dist = d2
                         best = (obj.x, obj.y)
                         
        return best
