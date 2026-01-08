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
        self.failed_targets = set() # (x,y) tuples that we failed to reach

    def execute(self, state: BrainState) -> List[Action]:
        actions = []
        
        # 1. Update Room Knowledge
        current_room_name = "Unknown"
        px, py = int(state.player.position.x), int(state.player.position.y)
        
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
            
        # 2. Check for Loot (Loot As You Go) - Placeholder
        pass

        # 3. Navigation & Arrival Check
        if self.nav_target:
            tx, ty = self.nav_target
            dist = math.dist((px, py), (tx, ty))
            
            # Stuck Detection
            if not hasattr(self, 'last_dist'): self.last_dist = dist
            if not hasattr(self, 'stuck_ticks'): self.stuck_ticks = 0
            
            if dist >= self.last_dist - 0.05: # Not moving closer
                self.stuck_ticks += 1
            else:
                self.stuck_ticks = 0
                self.last_dist = dist
                
            is_stuck = self.stuck_ticks > 15 # ~7.5 seconds stuck (increased to avoid false positives)
            
            # Arrival or Stuck
            if dist < 1.5 or is_stuck: 
                if is_stuck:
                    logger.warning(f"[SearchPlan] Stuck reaching {tx},{ty} (Dist: {dist:.1f}). Blacklisting target.")
                    self.failed_targets.add((tx, ty))
                else:
                    logger.info(f"[SearchPlan] Arrived at target {tx},{ty}")
                
                self.nav_target = None
                self.has_requested_move = False
                self.stuck_ticks = 0
                self.last_dist = 999
                
                if self.target_room and not is_stuck:
                    state.memory.visited_rooms.add(self.target_room)

        # 4. Pick Next Target
        if not self.nav_target:
            potential_targets = []
            for t in state.vision.tiles:
                # Filter invisible walls and failed targets
                if hasattr(t, 'v') and not t.v: continue
                if (t.x, t.y) in self.failed_targets: continue

                if hasattr(t, 'room') and t.room and t.room not in state.memory.visited_rooms:
                     potential_targets.append(t)
            
            if potential_targets:
                # Pick closest
                best = min(potential_targets, key=lambda t: math.dist((t.x, t.y), (px, py)))
                self.nav_target = (best.x, best.y)
                self.target_room = best.room
                self.last_dist = math.dist((best.x, best.y), (px, py))
                logger.info(f"[SearchPlan] Targeting new room: {best.room} at {best.x},{best.y}")
            else:
                # Check Stairs
                stairs_target = None
                if state.vision.objects:
                    for obj in state.vision.objects:
                        if "stairs" in str(obj.type).lower() or "stairs" in str(obj.id).lower():
                             stairs_target = obj
                             break
                
                if stairs_target and (stairs_target.x, stairs_target.y) not in self.failed_targets:
                    logger.info(f"[SearchPlan] Floor cleared. Targeting Stairs: {stairs_target.type}")
                    self.nav_target = (stairs_target.x, stairs_target.y)
                    self.target_room = "Stairs" 
                else:
                    # Check for exit? Or just finish?
                    if len(state.memory.visited_rooms) > 0:
                        logger.info("[SearchPlan] No new rooms or stairs. Finishing search.")
                        self.complete()
                        return []
                    else:
                        logger.info("[SearchPlan] Outside/No rooms found. Wandering.")
                        import random
                        dx = random.randint(-5, 5)
                        dy = random.randint(-5, 5)
                        self.nav_target = (px + dx, py + dy)

        # 5. Execute Navigation
        state.navigation.nav_target = self.nav_target
        if self.nav_target:
            tx, ty = self.nav_target
            
            obs_action = NavigatorHelper.check_for_obstacles(state, (tx, ty))
            if obs_action: return [obs_action]

            # DETERMINATE STANCE
            # If target room is already visited (backtracking) -> Run
            # If target room is Unknown/New -> Walk (or Aim if high caution)
            # If Urgency is high (Survival) -> Run/Sprint
            
            stance = "Auto"
            is_backtracking = self.target_room in state.memory.visited_rooms
            
            # Urgency Overrides
            # We don't have direct access to 'Needs' logic here easily without importing heavy logic,
            # but we can check state.situation
            mode = state.situation.current_mode if hasattr(state.situation, 'current_mode') else "IDLE"
            # Handle Enum wrapper if present
            if hasattr(mode, 'name'): mode = mode.name

            if mode == "SURVIVAL":
                stance = "Run" # Sprint might be too chaotic indoors
            elif is_backtracking:
                stance = "Run" # Quickly move through cleared areas
            else:
                stance = "Walk" # Measured pace for exploration
                # Future: "Aim" if gun equipped and high caution?
            
            if not hasattr(self, 'has_requested_move'): self.has_requested_move = False
            is_idle = state.player.action_state.status == "idle"
            
            if not self.has_requested_move or is_idle:
                dist = math.dist((px, py), (tx, ty))
                if dist > 0.5:
                    # logger.info(f"[SearchPlan] Move -> {tx},{ty} [{stance}]") 
                    actions.append(Action(ActionType.MOVE_TO.value, {
                        "x": tx, "y": ty, "z": 0,
                        "stance": stance
                    }))
                    self.has_requested_move = True
        
        return actions
