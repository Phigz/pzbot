def run(world):
    """
    Two stationary zombies nearby to test vision/combat.
    Runs for 10 seconds.
    """
    world.set_player_pos(100, 100)
    world.add_zombie(105, 100, "z1")
    world.add_zombie(100, 105, "z2")
    world.set_end_time(10.0)
