from bot_runtime.strategy.base import Strategy
from bot_runtime.brain.state import BrainState, SituationMode
from bot_runtime.control.action_queue import ActionQueue
import logging
from bot_runtime.planning.planner import ActionPlanner
from bot_runtime.planning.plans.loot_plan import LootPlan

from bot_runtime.planning.plans.investigate_plan import InvestigatePlan

logger = logging.getLogger(__name__)

class LootStrategy(Strategy):
    """
    Handles opportunisitic looting.
    Score: 50.0 if in OPPORTUNITY mode.
    Action: Set 'LootPlan' goal on Planner.
    """

    @property
    def name(self) -> str:
        return "Loot"

    def evaluate(self, state: BrainState) -> float:
        # Boost score slightly if we have a Preparedness Need
        base_score = 0.0
        if state.situation.current_mode == SituationMode.OPPORTUNITY:
            if state.situation.primary_driver == "Need Equipment":
                base_score = 70.0 # Higher priority than generic opportunity
            else:
                base_score = 50.0
        return base_score

    def execute(self, state: BrainState, queue: ActionQueue, planner: ActionPlanner = None):
        if not planner:
            # Fallback for old tests or direct usage
             queue.add("Wait", duration=100)
             return

        # 1. Check Specific Items (Floor or Known in Open Containers)
        targets = state.loot.high_value_targets
        
        if targets:
            # logger.info(f"[LOOT_STRAT] Targets found: {len(targets)}")
            best = targets[0] # Sorted by value
            target_id = best.get('id')
            if target_id:
                # If we are already doing this, Planner handles valid-check.
                # If we switch targets often, Planner might flap. 
                # Ideally check if 'active_plan' is same target.
                planner.set_goal(LootPlan(target_id=target_id))
                return

        # 2. Check Containers (Exploration)
        # If no items on floor/known, go check containers we think are valuable (or just nearby)
        container_targets = state.loot.container_targets
        
        if container_targets:
             best_cont = container_targets[0]
             # Don't investigate if completely empty?
             # But we might need to verify.
             # For now, just go to it.
             planner.set_goal(InvestigatePlan(best_cont['x'], best_cont['y'], 0, f"Container_{best_cont['id']}"))
             return
             
        logger.warning("[LOOT_STRAT] Active but NO targets!")
