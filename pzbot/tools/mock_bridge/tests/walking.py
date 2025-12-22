def run(world):
    """
    Simulates the player walking in a square pattern.
    Useful for testing the visualizer's camera/update smoothness.
    """
    start_x, start_y = 50, 50
    world.set_player_pos(start_x, start_y)
    
    # Create a simple floor for context
    for x in range(40, 60):
        for y in range(40, 60):
            world.set_tile(x, y, layer="Floor", room="outside")

    # Animation parameters
    duration = 20.0
    step_interval = 0.1
    speed = 2.0 # units per second
    
    # Define square path: (dx, dy, duration_segment)
    path_segments = [
        (1, 0, 5.0),  # Right
        (0, 1, 5.0),  # Down
        (-1, 0, 5.0), # Left
        (0, -1, 5.0)  # Up
    ]
    
    current_time = 0.0
    
    def make_mover(vel_x, vel_y, end_segment_time):
        def move_step():
            # Calculate next position
            # Note: We rely on the closure to keep track of current pos if we read from world
            # But world doesn't expose getters easily in this scope without reading state.
            # Simpler: just update based on previous known theoretical pos or read from state.
            
            # Read current pos from state to be safe (or maintain local state)
            c_x = world.player_x
            c_y = world.player_y
            
            n_x = c_x + (vel_x * step_interval * speed)
            n_y = c_y + (vel_y * step_interval * speed)
            
            world.set_player_pos(n_x, n_y)
            
            # Schedule next step if we haven't reached end of segment
            # We use world.sim_time + step_interval for next event
            if world.sim_time + step_interval < end_segment_time:
                 world.add_event(world.sim_time + step_interval, move_step)
                 
        return move_step

    # Schedule the segments
    segment_start_time = 0.0
    
    for dx, dy, seg_dur in path_segments:
        # Schedule the *first* step of this segment
        # The recursive 'move_step' will handle the rest until segment_end_time
        segment_end_time = segment_start_time + seg_dur
        
        mover = make_mover(dx, dy, segment_end_time)
        world.add_event(segment_start_time, mover)
        
        segment_start_time += seg_dur

    world.set_end_time(segment_start_time + 1.0)
