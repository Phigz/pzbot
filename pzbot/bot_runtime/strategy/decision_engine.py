import logging
from typing import List, Optional
from bot_runtime.brain.state import BrainState
from bot_runtime.control.action_queue import ActionQueue
from bot_runtime.strategy.base import Strategy

logger = logging.getLogger(__name__)

class DecisionEngine:
    """
    The 'Executive Function'.
    Evaluates all available strategies and executes the winner.
    """

    def __init__(self, action_queue: ActionQueue, planner=None):
        self.action_queue = action_queue
        self.planner = planner
        self.strategies: List[Strategy] = []
        self.active_strategy: Optional[Strategy] = None

    def register_strategy(self, strategy: Strategy):
        """Add a strategy to the pool."""
        self.strategies.append(strategy)
        logger.info(f"Registered Strategy: {strategy.name}")

    def decide(self, state: BrainState):
        """
        Main Decision Loop:
        1. Evaluate all strategies.
        2. Pick the highest score.
        3. Execute it.
        """
        if not self.strategies:
            return

        best_score = -1.0
        winner = None

        # 1. Evaluate
        for strategy in self.strategies:
            try:
                score = strategy.evaluate(state)
                # logger.debug(f"Strategy {strategy.name} score: {score}")
                
                if score > best_score:
                    best_score = score
                    winner = strategy
            except Exception as e:
                logger.error(f"Error evaluating strategy {strategy.name}: {e}")

        # 2. Transition & Log
        if winner and winner != self.active_strategy:
            logger.info(f"Decided Strategy: {winner.name} (Score: {best_score:.1f})")
            self.active_strategy = winner
        
        if self.active_strategy:
            state.active_strategy_name = self.active_strategy.name
        
        # 3. Execute
        if self.active_strategy:
            try:
                self.active_strategy.execute(state, self.action_queue, self.planner)
            except Exception as e:
                logger.error(f"Error executing strategy {self.active_strategy.name}: {e}")
