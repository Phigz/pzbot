import math
import logging
from typing import Tuple, List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class DirectMovementExecutor:
    """
    Handles the 'Dual Channel' movement logic.
    - Channel A (OS): Press 'W' to walk forward.
    - Channel B (File): Send 'LookAt' commands to rotate the character.
    """
    
    def __init__(self):
        self.alignment_threshold = 45.0 # Degrees within which we can walk
        self.stop_distance = 0.5 # Distance to stop
        
    def compute_actions(self, 
                        player_pos: Dict[str, float], 
                        player_rot: float, 
                        target_pos: Dict[str, float]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Returns a tuple of (OS_Actions, File_Actions).
        """
        
        px, py = player_pos.get('x', 0), player_pos.get('y', 0)
        tx, ty = target_pos.get('x', 0), target_pos.get('y', 0)
        
        dx = tx - px
        dy = ty - py
        dist = math.sqrt(dx*dx + dy*dy)
        
        os_actions = []
        file_actions = []
        
        if dist <= self.stop_distance:
            return os_actions, file_actions
            
        # 1. Calculate Target Angle (Degrees, 0=Right/East, CW? PZ uses vector angle)
        # PZ getDirectionAngle(): 0=East, 90=South (CHECK THIS)
        # Standard atan2: 0=East, Positive=CounterCW? 
        # We need to match PZ coordinate system.
        # PZ: X increases East, Y increases South.
        # atan2(dy, dx) -> if Y is down, 
        # (1, 1) -> atan2(1, 1) = 45 deg = SouthEast. Matches?
        
        target_angle_rad = math.atan2(dy, dx)
        target_angle_deg = math.degrees(target_angle_rad)
        
        # 2. Emit LookAt Command (Channel B)
        # We send the World Coordinate to look at. Lua handles the rotation.
        # We throttle this? No, Controller throttles file writes. 
        # Ideally we only send if target changes significantly or we aren't aiming there.
        # But for now, stateless is easier.
        file_actions.append({
            "type": "FaceLocation", # or LookAt
            "params": { "x": tx, "y": ty }
        })
        
        # 3. Check Alignment for Movement (Channel A)
        # We need player's current angle.
        # Assumption: player_rot is in Degrees.
        
        # Normalize diff to -180..180
        diff = target_angle_deg - player_rot
        while diff > 180: diff -= 360
        while diff <= -180: diff += 360
        
        alignment = abs(diff)
        
        # If we are roughly facing the target, walk.
        # If we are wildly off, maybe wait for turn? 
        # Turning while walking in PZ is slow/wide arc. 
        # Turning while standing is fast.
        # So: If alignment > 90, ONLY Turn. If < 90, Walk + Turn.
        
        if alignment < 90:
            # Walk Forward
            # Should we Sprint? That's up to the Plan/Strategy. 
            # Executor just moves. 
            # We can accept a 'speed' param later.
            os_actions.append({
                "type": "DirectMove",
                "params": {
                    "direction": "w",
                    "duration": 0.25 # Short burst, Controller ticks frequently?
                }
            })
            
        return os_actions, file_actions
