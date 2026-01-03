from typing import List, Optional, Set
import math
import logging

from bot_runtime.brain.state import BrainState
from bot_runtime.control.action_queue import Action, ActionType
from bot_runtime.planning.base import Plan, PlanStatus
from bot_runtime.planning.plans.loot_plan import LootPlan

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
        self.visited_rooms: Set[str] = set()
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
            if current_room_name not in self.visited_rooms:
                logger.info(f"[SearchPlan] Discovered Room: {current_room_name}")
                self.visited_rooms.add(current_room_name)
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
                if hasattr(t, 'room') and t.room and t.room not in self.visited_rooms:
                     potential_targets.append(t)
            
            if potential_targets:
                # Pick closest
                best = min(potential_targets, key=lambda t: math.dist((t.x, t.y), (px, py)))
                self.nav_target = (best.x, best.y)
                self.target_room = best.room
                logger.info(f"[SearchPlan] Targeting new room: {best.room} at {best.x},{best.y}")
            else:
                # No unvisited rooms visible. 
                # Explore blindly? Or finish?
                # If we explored the whole house, we are done.
                if len(self.visited_rooms) > 0:
                    logger.info("[SearchPlan] No new rooms visible. Finishing search.")
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
            dist = math.dist((px, py), (tx, ty))
            if dist < 1.1: # Increased threshold slightly
                self.nav_target = None # Arrived
                self.has_requested_move = False # Reset for next leg
                logger.info(f"[SearchPlan] Arrived at target {tx},{ty}")
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
                    return actions # Return immediately to avoid logic conflicts
                
        return actions
