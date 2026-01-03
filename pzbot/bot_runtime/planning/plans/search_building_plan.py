from typing import List, Optional, Set
import math
import logging

from bot_runtime.brain.state import BrainState
from bot_runtime.control.action_queue import Action, ActionType
from bot_runtime.planning.base import Plan, PlanStatus
from bot_runtime.planning.plans.loot_plan import LootPlan
from bot_runtime.planning.utils.navigator_helper import NavigatorHelper

logger = logging.getLogger(__name__)

class SearchBuildingPlan(Plan):
    """
    Systematic exploration of a building.
    Mode: 
     - LOOT_AS_YOU_GO: If we see loot, pause search and loot it.
     - CLEAR_FIRST: Visit all rooms first.
    """
    
    def __init__(self, start_x: int, start_y: int, mode="LOOT_AS_YOU_GO"):
        super().__init__(f"SearchBuilding({start_x},{start_y})")
        self.mode = mode
        # self.visited_rooms is now in state.memory.visited_rooms
        self.known_rooms = {} # name -> center_pos {x,y}
        self.current_room = None
        
        self.target_room = None
        self.nav_target = None
        
    def execute(self, state: BrainState) -> List[Action]:
        actions = []
        
        # 1. Update Room Knowledge
        # In future, Sensor should return specific room ID/Name at current pos
        # For now, we rely on `vision.tiles` or a `current_room` field if available
        # Current fallback: assume we are in "Unknown" unless Sensor tells us.
        
        # HACK: Infer room from nearby tiles
        current_room_name = "Unknown"
        px, py = int(state.player.position.x), int(state.player.position.y)
        
        # Check current tile room
        # We need to rely on what Sensor sees. 
        # Ideally, Sensor.lua sends `state.player.room`?
        # Let's check `state.player` schema? 
        # Assuming we can derive it or it's not there yet. 
        # Plan B: Look at `vision.tiles` under feet.
        
        for t in state.vision.tiles:
            if int(t.x) == px and int(t.y) == py:
                if hasattr(t, 'room') and t.room:
                    current_room_name = t.room
                break
        
        if current_room_name != "Unknown":
            if current_room_name not in state.memory.visited_rooms:
                logger.info(f"[SearchPlan] Discovered Room: {current_room_name}")
                state.memory.visited_rooms.add(current_room_name)
            self.current_room = current_room_name
            
        # 2. Check for Loot (Loot As You Go)
        if self.mode == "LOOT_AS_YOU_GO":
            # Delegate to LootStrategy logic? 
            # Or just check if we see something we WANT (Needs based).
            # For simplicity: If we see a Dresser/Wardrobe and we need clothes, 
            # we suspend this plan and push a LootPlan?
            # Actually, `execute` returns actions. We can't easily "push" a sub-plan here 
            # unless the Planner supports stack.
            # Workaround: Return NO actions, but set a flag that Strategy picks up next tick? 
            # Better: This Plan finishes if it finds something good?
            pass

        # 3. Pick Next Target
        if not self.nav_target:
            # logic to find next room
            # We need a list of "Unvisited Connected Rooms".
            # Sensor doesn't give us a topo map.
            # Heuristic: Walk to nearest "Door" that leads to unvisited area?
            # Or just random walk to unvisited tiles?
            
            # Simple approach: Find a Door in Vision we haven't passed through?
            # Too complex for MVP.
            
            # MVP Approach:
            # 1. List all rooms visible in `vision.tiles`
            # 2. Pick one that is NOT in `visited_rooms`.
            # 3. Move to it.
            
            potential_targets = []
            for t in state.vision.tiles:
                if hasattr(t, 'room') and t.room and t.room not in state.memory.visited_rooms:
                     potential_targets.append(t)
            
            if potential_targets:
                # Pick closest
                best = min(potential_targets, key=lambda t: math.dist((t.x, t.y), (px, py)))
                self.nav_target = (best.x, best.y)
                self.target_room = best.room
                logger.info(f"[SearchPlan] Targeting new room: {best.room} at {best.x},{best.y}")
            else:
                # No unvisited rooms visible on this floor.
                # Check for Stairs to change floor?
                # We only do this if we have visited at least ONE room on this floor to avoid instant stair climbing.
                
                stairs_target = None
                if state.vision.objects:
                    player_z = state.player.position.z
                    for obj in state.vision.objects:
                        if "stairs" in str(obj.type).lower() or "stairs" in str(obj.id).lower():
                             # Ensure we haven't just used this stair (ping-pong prevention?)
                             # For now, just go to it if it looks valid
                             
                             # Check if it leads UP or DOWN?
                             # Usually stairs are on current floor and lead up, or current floor (void) leading down.
                             # If we are on Z=0, we look for stairs.
                             
                             # Distance check
                             stairs_target = obj
                             break
                
                if stairs_target:
                    logger.info(f"[SearchPlan] Floor cleared. Targeting Stairs: {stairs_target.type} at {stairs_target.x},{stairs_target.y}")
                    self.nav_target = (stairs_target.x, stairs_target.y)
                    self.target_room = "Stairs" # Mock room name
                else:
                    if len(state.memory.visited_rooms) > 0:
                        logger.info("[SearchPlan] No new rooms or stairs visible. Finishing search.")
                        self.complete()
                        return []
                    else:
                        # We haven't found ANY rooms yet (maybe outside?)
                        logger.info("[SearchPlan] Outside/No rooms found. Wandering.")
                        # Random walk?
                        import random
                        dx = random.randint(-5, 5)
                        dy = random.randint(-5, 5)
                        self.nav_target = (px + dx, py + dy)

        # 4. Navigate
        if self.nav_target:
            tx, ty = self.nav_target
            
            # OBSTACLE CHECK (Weaving)
            obs_action = NavigatorHelper.check_for_obstacles(state, (tx, ty))
            if obs_action:
                 return [obs_action]

            dist = math.dist((px, py), (tx, ty))
            if dist < 1.1: # Increased threshold slightly
                self.nav_target = None # Arrived
                self.has_requested_move = False # Reset for next leg
                logger.info(f"[SearchPlan] Arrived at target {tx},{ty}")
                
                # Mark target room as visited to prevent loops if we are close but not "on" the tile
                if self.target_room:
                    logger.info(f"[SearchPlan] Marked target room {self.target_room} as visited.")
                    state.memory.visited_rooms.add(self.target_room)
                    
                # We are now in the room (hopefully). 
                # Next tick will register it as visited.
            else:
                # Emit Move ONLY if not moving or idle
                # We need to track if we already sent it.
                if not hasattr(self, 'has_requested_move'): self.has_requested_move = False
                
                is_idle = state.player.action_state.status == "idle"
                
                if not self.has_requested_move or is_idle:
                    logger.info(f"[SearchPlan] Requesting Move to {tx},{ty} (Dist: {dist:.1f})")
                    # Emit Move
                    actions.append(Action(ActionType.MOVE_TO.value, {
                        "x": tx, "y": ty, "z": 0,
                        "stance": state.situation.recommended_stance
                    }))
                    self.has_requested_move = True
                else:
                    # We are waiting for move to complete?
                    if self.has_requested_move and not is_idle:
                        pass
                        # logger.debug(f"[SearchPlan] Waiting for move... Status: {state.player.action_state.status}")
                    elif self.has_requested_move and is_idle:
                        # We requested move, but are now idle. Did we stop?
                        # This state usually flips has_requested_move back to False if we arrived, 
                        # but we are in the 'else' block of dist < 1.1, so we are NOT arrived.
                        # Has the action failed?
                        logger.warning(f"[SearchPlan] Idle but not arrived (Dist:{dist:.1f}). Re-requesting move.")
                        self.has_requested_move = False
        
        return actions
