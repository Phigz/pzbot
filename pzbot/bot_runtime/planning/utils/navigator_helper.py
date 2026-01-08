import math
import logging
from typing import Optional, Tuple

from bot_runtime.brain.state import BrainState
from bot_runtime.control.action_queue import Action, ActionType

logger = logging.getLogger(__name__)

class NavigatorHelper:
    """
    Provides reactive navigation logic to handle obstacles that native pathfinding
    might miss or get stuck on (e.g. Closed Doors, Windows, Fences).
    """

    @staticmethod
    def check_for_obstacles(state: BrainState, target_pos: Tuple[float, float]) -> Optional[Action]:
        """
        Scans for immediate obstacles between player and target.
        Returns an Interaction Action if an obstacle is found, else None.
        """
        if not state.player or not state.vision:
            return None
            
        px, py = state.player.position.x, state.player.position.y
        tx, ty = target_pos
        
        # Vector to target
        dx = tx - px
        dy = ty - py
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist < 0.1: return None
        
        # Normalize
        ndx, ndy = dx/dist, dy/dist
        
        # Look ahead distance (scan roughly 4.0 tiles ahead)
        SCAN_DIST = 4.0
        
        # We check objects in vision
        # Ideally we only check objects that intersect our vector or are VERY close.
        # Simple heuristic: Check objects within SCAN_DIST of player.
        
        if not state.vision.objects:
            logger.debug("[NavHelper] No objects in vision.")
            return None
            
        logger.debug(f"[NavHelper] Scanning {len(state.vision.objects)} objects. P({px:.1f},{py:.1f}) -> T({tx:.1f},{ty:.1f})")
            
        for obj in state.vision.objects:
            # Check ID/Type to confirm it's an obstacle
            o_type = obj.type # e.g. IsoDoor, IsoWindow, IsoThumpable
            
            # Filter for Interactables
            is_door = "Door" in o_type
            is_window = "Window" in o_type
            
            if not (is_door or is_window):
                continue
                
            # Check Position
            ox, oy = obj.x, obj.y
            
            # Z-Level Check
            # Assuming player.z is float but often integer value. 
            # Obstacles must be on same Z to block us.
            obj_z = getattr(obj, 'z', 0)
            player_z = state.player.position.z
            if int(obj_z) != int(player_z):
                continue
            
            # Distance to object
            
            # Distance to object
            obj_dist = math.dist((px, py), (ox, oy))
            
            if obj_dist > SCAN_DIST:
                continue
            # Check if obstacle is further than our target (e.g. target is in front of window)
            if obj_dist > dist + 0.5:
                # logger.debug(f"[NavHelper] Skipping {o_type} (Dist:{obj_dist:.1f} > Tgt:{dist:.1f})")
                continue

            # Check if it's actually "Open"
            # Schema: obj.flags might contain 'open' or specific fields?
            # Looking at Input Parser (Sensor.lua->Python), we usually get specific fields.
            # Let's assume we can check `obj.is_open` or strictly parsed flags.
            # If the model doesn't have it, we might rely on the `PathCost` logic which is Lua side.
            # But here we are Python side.
            # Let's inspect `obj` properties. `obj` is of type `WorldObject` from `state.py` (via `Vision`).
            # We need to ensure `is_open` is populated. 
            
            # Assuming `is_open` attribute exists on the Pydantic model for objects.
            # If not, we might check `sprites` or `flags`.
            # For now, let's assume `is_open` boolean is available or we check regex on sprite name if available.
            
            is_closed = True
            
            # Check Meta for Open status (populated by Sensor.lua)
            if obj.meta and obj.meta.get('open'):
                is_closed = False
                
            # Legacy/Fallback checks
            elif hasattr(obj, 'is_open') and obj.is_open:
                is_closed = False
            elif hasattr(obj, 'flags') and 'open' in (obj.flags or []): 
                is_closed = False
                
            if not is_closed:
                continue
                
            # It is a closed door/window near us.
            # Is it in our path?
            # Dot Product check: (Object - Player) . (Target - Player)
            # If > 0.8 (approx 45 deg cone), it's in front.
            
            odx, ody = ox - px, oy - py
            odist = math.sqrt(odx*odx + ody*ody)
            if odist == 0: continue
            
            nodx, nody = odx/odist, ody/odist
            
            # Stricter Check: Distance from object to path segment (Player -> Target)
            # If the object is within X distance of the line segment, it's a blocker.
            # And it must be between Player and Target (projected point on segment).
            
            # Vector Player->Target
            # dx, dy, dist are already calculated for Player->Target
            
            # Vector Player->Object
            odx, ody = ox - px, oy - py
            
            # Project Object onto Player->Target vector
            # ret = (odx * dx + ody * dy) / (dist * dist)
            if dist == 0: ret = 0
            else: ret = (odx * dx + ody * dy) / (dist * dist)
            
            # Check if projection falls on the segment [0, 1]
            # We add a small buffer so we detect obstacles JUST behind us or JUST ahead (handled partially by loop checks)
            if ret < 0 or ret > 1:
                # The closest point on the line is outside our path segment
                continue
                
            # Closest point on signal
            closest_x = px + ret * dx
            closest_y = py + ret * dy
            
            # Distance from Object center to that closest point
            dist_to_line = math.dist((ox, oy), (closest_x, closest_y))
            
            # Threshold: Object Radius. 
            # A Window/Door is usually 1 tile wide. Center is at 0.5.
            # If we pass within 0.5 of its center, we might hit it.
            # Let's say 0.6 to be safe.
            if dist_to_line < 0.6:
                logger.info(f"[NavHelper] Obstacle Detected: {o_type} at {ox},{oy}. DistLine:{dist_to_line:.2f}")
                return Action(ActionType.INTERACT.value, {
                    "targetId": obj.id
                })
                
        return None
