import logging
from typing import Optional
from bot_runtime.ingest.state import GameState
from bot_runtime.world.model import WorldModel
from bot_runtime.control.action_queue import ActionQueue
from bot_runtime.io.input_writer import InputWriter
from bot_runtime.world.logger import WorldLogger

logger = logging.getLogger(__name__)

from bot_runtime.brain.brain import Brain

logger = logging.getLogger(__name__)

class BotController:
    def __init__(self, world_model: WorldModel, action_queue: ActionQueue, input_writer: InputWriter):
        self.world_model = world_model
        self.action_queue = action_queue
        self.input_writer = input_writer
        
        self.world_logger = WorldLogger(self.world_model)
        
        # Initialize The Brain
        self.brain = Brain(self.world_model)

    def on_tick(self, game_state: GameState):
        """Called whenever a new game state is received."""
        # 1. Update World Model
        self.world_model.update(game_state)

        # 2. Update Brain (Analysis)
        self.brain.update()

        # 3. Log World Status
        self.world_logger.update()
        
        # 4. Log Brain Activity (Throttle to every ~2s / 20 ticks)
        if self.world_model.tick_count % 20 == 0:
            b = self.brain.state
            
            # Threat
            t_lvl = b.threat.global_level
            t_vec = len(b.threat.vectors)
            
            # Needs
            needs_str = ", ".join([f"{n.name}:{n.score:.0f}" for n in b.needs.active_needs]) or "None"
            
            # Recent Thought
            last_thought = b.active_thought.message if b.active_thought else "..."
            
            logger.info(f"[CORTEX] Threat: {t_lvl:.1f}% ({t_vec} vec) | Needs: [{needs_str}] | Thought: \"{last_thought}\"")
            
            # Log Vitals specifically as requested
            if game_state.player and game_state.player.body:
                body = game_state.player.body
                # Sanitize scale (if > 1.0 assume 0-100 scale)
                hp = body.health if body.health <= 1.0 else body.health / 100.0
                stam = body.stamina if body.stamina <= 1.0 else body.stamina / 100.0
                hung = body.hunger if body.hunger <= 1.0 else body.hunger / 100.0
                thirst = body.thirst if body.thirst <= 1.0 else body.thirst / 100.0
                
                logger.info(f"[VITALS] HP:{hp*100:.0f}% Stamina:{stam*100:.0f}% Hunger:{hung*100:.0f}% Thirst:{thirst*100:.0f}%")

        # 5. Flush Action Queue to Input Writer
        # DISABLED for World Model building phase - Pure Observer Mode
        # if self.action_queue.has_actions():
        #     actions = self.action_queue.pop_all()
        #     logger.info(f"Flushing {len(actions)} actions.")
        #     self.input_writer.write_actions(actions)
