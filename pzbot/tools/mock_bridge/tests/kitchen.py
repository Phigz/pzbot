def run(world):
    """
    Simulates finding a kitchen.
    Time 0s: Outside house.
    Time 2s: "Enters" kitchen (teleport).
    Time 2.1s: Sees containers.
    Time 5s: Ends.
    """
    # T=0
    world.set_player_pos(100, 100) # Outside
    
    # helper for entering kitchen
    def enter_kitchen():
        world.set_player_pos(50, 50) # "Kitchen" coords
        
        # Build Kitchen (5x5 room from 48,48 to 52,52)
        # Floor
        for x in range(48, 53):
            for y in range(48, 53):
                world.set_tile(x, y, layer="Floor", room="Kitchen", walkable=True)
                
        # Walls (North and South)
        for x in range(48, 53):
            world.set_tile(x, 47, layer="Wall", room="Kitchen", walkable=False)
            world.set_tile(x, 53, layer="Wall", room="Kitchen", walkable=False)
            
        # Walls (East and West)
        for y in range(48, 53):
            world.set_tile(47, y, layer="Wall", room="Kitchen", walkable=False)
            world.set_tile(53, y, layer="Wall", room="Kitchen", walkable=False)

    def spawn_fridge():
        # Inject container directly into state
        world.state["environment"]["nearby_containers"].append({
            "type": "Container", 
            "object_type": "Fridge",
            "x": 51, "y": 50, "z": 0,
            "items": [{"type": "Food", "name": "Steak", "count": 1}]
        })

    world.add_event(2.0, enter_kitchen)
    world.add_event(2.1, spawn_fridge)
    
    world.set_end_time(5.0)
