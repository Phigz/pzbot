def run(world):
    """
    Testing fleeing logic.
    Runs for 15 seconds.
    """
    world.set_player_pos(100, 100)
    world.add_zombie(102, 100, "n")
    world.add_zombie(98, 100, "s")
    world.add_zombie(100, 102, "e")
    world.add_zombie(100, 98, "w")
    world.set_end_time(15.0)
