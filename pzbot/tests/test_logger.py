import unittest
import logging
from unittest.mock import MagicMock
from bot_runtime.world.logger import WorldLogger
from bot_runtime.world.view import WorldView
from bot_runtime.ingest.state import Player, Position
from bot_runtime.world.types import EntityData

class TestWorldLogger(unittest.TestCase):
    def test_log_output(self):
        # Mock the WorldView
        mock_view = MagicMock(spec=WorldView)
        
        # Mock Player
        p = MagicMock(spec=Player)
        p.position = Position(x=100, y=100, z=0)
        mock_view.player = p
        
        # Mock Entities
        mock_view.get_entities.return_value = [
            EntityData(id="z1", type="Zombie", x=105, y=100, z=0, properties={"state": "chasing"}),
            EntityData(id="p2", type="Player", x=102, y=100, z=0, properties={})
        ]
        
        # Mock Nearest
        mock_view.find_nearest_entity.return_value = EntityData(id="z1", type="Zombie", x=105, y=100, z=0)
        
        # Capture logs
        with self.assertLogs('bot_runtime.world.logger', level='INFO') as cm:
            logger = WorldLogger(mock_view, log_interval=0.0) # 0 interval to force log
            logger.update()
            
            self.assertTrue(len(cm.output) > 0)
            log_msg = cm.output[0]
            
            # Verify content
            self.assertIn("Player @ (100.0, 100.0, 0.0)", log_msg)
            self.assertIn("Zombies: 2", log_msg) # Since get_entities returns list of length 2 (wait, I used same list for all calls?)
            
        # Refine mock for get_entities specific calls
        def get_ents_side_effect(type_filter=None):
            if type_filter == "Zombie":
                return [EntityData(id="z1", type="Zombie", x=0, y=0, z=0)]
            if type_filter == "Player":
                return []
            return []
            
        mock_view.get_entities.side_effect = get_ents_side_effect
        
        with self.assertLogs('bot_runtime.world.logger', level='INFO') as cm:
            logger = WorldLogger(mock_view, log_interval=0.0)
            logger.update()
            self.assertIn("Zombies: 1", cm.output[0])

if __name__ == '__main__':
    unittest.main()
