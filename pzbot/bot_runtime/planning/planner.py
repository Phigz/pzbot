from typing import List, Optional
import logging

from bot_runtime.brain.state import BrainState
from bot_runtime.control.action_queue import Action
from bot_runtime.planning.base import Plan, PlanStatus

logger = logging.getLogger(__name__)

class ActionPlanner:
    """
    Tier 3.5 System.
    Manages the lifecycle of persistent Plans (FSMs).
    """
    def __init__(self):
        self.active_plan: Optional[Plan] = None
        
    def is_idle(self) -> bool:
        return self.active_plan is None

        
    def set_goal(self, plan: Plan, force: bool = False):
        """
        Assigns a new plan.
        If a plan is already running, this will overwrite it based on logic 
        (currently simple overwrite, but could add priority checks).
        """
        if self.active_plan:
            if self.active_plan.status == PlanStatus.RUNNING and not force:
                if self.active_plan.name == plan.name:
                    # Same plan type, maybe just let it run?
                    # For now, always overwrite to ensure responsiveness to new goals
                    # But if we want persistence (e.g. don't reset Loot progress), we would check params.
                    pass
        
        logger.info(f"[PLANNER] Setting new goal: {plan.name} ({plan.id})")
        self.active_plan = plan
        
    def update(self, state: BrainState) -> List[Action]:
        """
        Called every tick. Advances the active plan.
        """
        if not self.active_plan:
            return []
            
        plan = self.active_plan
        
        # If plan is finished/failed, clear it
        if plan.status in [PlanStatus.COMPLETE, PlanStatus.FAILED]:
            logger.info(f"[PLANNER] Plan {plan.name} ended: {plan.status}")
            self.active_plan = None
            return []
            
        # Execute logic
        try:
            if plan.status == PlanStatus.PENDING:
                plan.status = PlanStatus.RUNNING
                
            actions = plan.execute(state)
            
            # Check status again after execution
            if plan.status == PlanStatus.FAILED:
                logger.warning(f"[PLANNER] Plan {plan.name} Failed: {plan.error_message}")
                
            return actions
            
        except Exception as e:
            logger.error(f"[PLANNER] Critical error in plan {plan.name}: {e}", exc_info=True)
            plan.fail(f"Exception: {e}")
            return []
