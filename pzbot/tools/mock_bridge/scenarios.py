def scenario_empty_room(world):
    """
    Standard empty room for testing navigation.
    """
    world.set_player_pos(100, 100)
    # No zombies

def scenario_basic_zombies(world):
    """
    Two stationary zombies nearby to test vision/combat.
    """
    world.set_player_pos(100, 100)
    world.add_zombie(105, 100, "z1")
    world.add_zombie(100, 105, "z2")

def scenario_surrounded(world):
    """
    Testing fleeing logic.
    """
    world.set_player_pos(100, 100)
    world.add_zombie(102, 100, "n")
    world.add_zombie(98, 100, "s")
    world.add_zombie(100, 102, "e")
    world.add_zombie(100, 98, "w")

SCENARIO_MAP = {
    "empty": scenario_empty_room,
    "basic": scenario_basic_zombies,
    "surrounded": scenario_surrounded
}
