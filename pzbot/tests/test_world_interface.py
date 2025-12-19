import unittest
import time
from bot_runtime.world.model import WorldModel
from bot_runtime.world.view import WorldView
from bot_runtime.ingest.state import GameState, Player, Vision
from bot_runtime.world.types import EntityData
from pydantic import BaseModel

class TestWorldInterface(unittest.TestCase):
    def test_protocol_compliance(self):
        """Check if WorldModel effectively implements WorldView."""
        model = WorldModel()
        self.assertIsInstance(model, WorldView)

    def test_entity_queries(self):
        model = WorldModel()
        
        # Inject fake entity
        model.entities.update_entity("z_1", "Zombie", 10, 10, 0)
        model.entities.update_entity("z_2", "Zombie", 20, 20, 0)
        model.entities.update_entity("p_1", "Player", 15, 15, 0)
        
        # Test get_entities
        all_ents = model.get_entities()
        self.assertEqual(len(all_ents), 3)
        
        zombies = model.get_entities("Zombie")
        self.assertEqual(len(zombies), 2)
        
        # Test find_nearest
        # (15,15) is exactly where p_1 is. Distance 0.
        nearest = model.find_nearest_entity(15, 15)
        self.assertIsNotNone(nearest)
        self.assertEqual(nearest.id, "p_1")
        
        # Test find_nearest with filter
        # Nearest Zombie to (15,15) is z_1 at (10,10) (dist 7.07) vs z_2 at (20,20) (dist 7.07)
        # Actually dist sq: (10-15)^2 + (10-15)^2 = 25+25 = 50.
        # (20-15)^2 + (20-15)^2 = 25+25 = 50.
        # Tie. Order depends on dict iteration order.
        
        # Let's move query point closer to z_1
        nearest_z = model.find_nearest_entity(11, 11, "Zombie")
        self.assertEqual(nearest_z.id, "z_1")

    def test_vision_age(self):
        model = WorldModel()
        self.assertEqual(model.get_vision_age(), float('inf'))
        
        # Update
        fake_state = GameState(
            timestamp=123,
            tick=1.0,
            player=Player(
                status="idle",
                position={"x":0,"y":0,"z":0},
                rotation=0,
                state={},
                body={"health":100}, # Minimal required fields
                moodles={},
                inventory={"held":{}, "worn":[], "main":[]},
                vision=Vision(scan_radius=10, timestamp=123, tiles=[], objects=[]),
                action_state={}
            )
        )
        model.update(fake_state)
        
        age = model.get_vision_age()
        self.assertLess(age, 0.1)
        self.assertGreaterEqual(age, 0.0)

if __name__ == '__main__':
    unittest.main()
