from bot_runtime.strategy.base import Strategy
from bot_runtime.brain.state import BrainState, SituationMode
from bot_runtime.control.action_queue import ActionQueue
from bot_runtime.planning.planner import ActionPlanner
from bot_runtime.planning.plans.search_building_plan import SearchBuildingPlan
from bot_runtime.planning.base import PlanStatus

import logging
logger = logging.getLogger(__name__)

class LootBuildingStrategy(Strategy):
    """
    Complex strategy to Assess, Enter, and Clear a building.
    Prototype Phase 2.
    """
    
    # FSM States
    STATE_ASSESS = "ASSESS"
    STATE_FIND_TARGET = "FIND_TARGET"
    STATE_GAIN_ENTRY = "GAIN_ENTRY"
    STATE_CLEAR_INTERIOR = "CLEAR_INTERIOR"
    STATE_EXIT = "EXIT"

    def __init__(self):
        self.current_fsm_state = self.STATE_ASSESS
        self.building_target = None

    @property
    def name(self) -> str:
        return "LootBuilding"

    def evaluate(self, state: BrainState) -> float:
        # Require valid player position
        if int(state.player.position.x) == 0 and int(state.player.position.y) == 0:
            return 0.0

        # High score if explicitly requested or in OPPORTUNITY/SAFETY mode with no urgent threats
        if state.situation.current_mode == SituationMode.OPPORTUNITY:
            return 80.0
        return 0.0

    def execute(self, state: BrainState, queue: ActionQueue, planner: ActionPlanner = None):
        if not planner:
            logger.warning("[LootBuilding] No Planner available.")
            queue.add("Wait", duration=50)
            return

        # FSM LOGIC
        if self.current_fsm_state == self.STATE_ASSESS:
            self.do_assess(state, planner)
            
        elif self.current_fsm_state == self.STATE_FIND_TARGET:
            self.do_find_target(state, planner)
            
        elif self.current_fsm_state == self.STATE_GAIN_ENTRY:
             pass # Not implemented yet
             
        elif self.current_fsm_state == self.STATE_CLEAR_INTERIOR:
            self.do_clear_interior(state, planner)
            
        elif self.current_fsm_state == self.STATE_EXIT:
            logger.info("[LootBuilding] Strategy Complete.")
            # Reset for next time? Or stay done?
            # For now, stay done (score will drop in real logic, or we reset)
            self.current_fsm_state = self.STATE_ASSESS 
            queue.add("Wait", duration=100)

    def do_assess(self, state: BrainState, planner: ActionPlanner):
        # Am I inside?
        is_inside = False
        
        # 1. Check Player room (if available)
        # 2. Check Tiles
        px, py = int(state.player.position.x), int(state.player.position.y)


        if state.vision and state.vision.tiles:
            # Debug: Scan 3x3 around player to see if ANY have room
            found_rooms = []
            for t in state.vision.tiles:
                if abs(t.x - px) <= 1 and abs(t.y - py) <= 1:
                     if hasattr(t, 'room') and t.room:
                         found_rooms.append(f"{t.x},{t.y}:{t.room}")
                         if t.x == px and t.y == py:
                             is_inside = True
            
            if found_rooms:
                logger.debug(f"[LootBuilding] Player at {px},{py}. Nearby Rooms: {found_rooms}")
            else:
                logger.debug(f"[LootBuilding] Player at {px},{py}. No rooms in 3x3 tiles.")     
                     
        if is_inside:
            logger.info(f"[LootBuilding] Confirmed Inside based on tile at {px},{py}")
                     
        if is_inside:
            logger.info("[LootBuilding] State -> CLEAR_INTERIOR")
            self.current_fsm_state = self.STATE_CLEAR_INTERIOR
        else:
            logger.info("[LootBuilding] State -> FIND_TARGET")
            self.current_fsm_state = self.STATE_FIND_TARGET

    def do_find_target(self, state: BrainState, planner: ActionPlanner):
        # Prototype: Do we see a building?
        # Use GeoAnalyzer (Mock)
        # For prototype, just log and wait.
        logger.info("[LootBuilding] Looking for target building... (Not Implemented)")
        planner.active_plan = None # Idle
        
    def do_clear_interior(self, state: BrainState, planner: ActionPlanner):
        # Ensure SearchPlan is running
        
        current_plan = planner.active_plan
        
        # Check if we finished
        if current_plan and current_plan.name.startswith("SearchBuilding") and current_plan.status == PlanStatus.COMPLETE:
            logger.info("[LootBuilding] Interior Cleared.")
            self.current_fsm_state = self.STATE_EXIT
            return

        # Check if we are running something else unrelated?
        if current_plan and not current_plan.name.startswith("SearchBuilding") and not current_plan.name.startswith("Loot"):
             # Interrupted by something?
             pass
             
        # If not running Search, start it
        if not current_plan or (current_plan.status != PlanStatus.RUNNING and not current_plan.name.startswith("SearchBuilding")):
             px, py = int(state.player.position.x), int(state.player.position.y)
             logger.info("[LootBuilding] Starting SearchBuildingPlan")
             planner.set_goal(SearchBuildingPlan(px, py, mode="LOOT_AS_YOU_GO"))
