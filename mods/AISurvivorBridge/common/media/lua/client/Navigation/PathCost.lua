-- Navigation/PathCost.lua
-- Calculates the traversal cost for a given square
local PathCost = {}

-- Constants
PathCost.COST_WALK = 1
PathCost.COST_DOOR_CLOSED = 5
PathCost.COST_DOOR_LOCKED = 9999 -- Treat as blockade
PathCost.COST_WINDOW_CLOSED = 10
PathCost.COST_WINDOW_LOCKED = 9999
PathCost.COST_ZOMBIE = 20
PathCost.COST_BLOCKED = 9999
-- Penalty for moving diagonally? usually roughly 1.41, but we can simplify or rely on Euclidean heuristic.

function PathCost.getCost(sq)
    if not sq then return PathCost.COST_BLOCKED end
    
    -- 1. Basic Walkability
    if not sq:isFree(false) then
        -- Check if it's a door/window that we can interact with
        -- isFree(false) often returns false for closed doors/windows
    end

    -- We need to check objects on the square
    local cost = PathCost.COST_WALK
    
    -- Check Objects
    local objects = sq:getObjects()
    for i=0, objects:size()-1 do
        local obj = objects:get(i)
        
        -- DOOR
        if instanceof(obj, "IsoDoor") then
            if obj:isLocked() or obj:isLockedByKey() then
                return PathCost.COST_DOOR_LOCKED
            end
            if not obj:IsOpen() then
                cost = cost + PathCost.COST_DOOR_CLOSED
            end
        end
        
        -- WINDOW
        if instanceof(obj, "IsoWindow") then
             -- Logic for windows is tricky, they are usually on the edge.
             -- isFree check usually handles wall/window collisions. 
             -- But if we want to climb through, we need to know.
             if obj:isLocked() or obj:isPermaLocked() then
                 -- Can we open it? 
                 return PathCost.COST_WINDOW_LOCKED
             end
             if not obj:getSprite() or not obj:getSprite():getName() or not string.find(tostring(obj:getSprite():getName()), "open") then
                 cost = cost + PathCost.COST_WINDOW_CLOSED
             end
        end
        
        -- THUMPABLE (Player built walls/doors)
        if instanceof(obj, "IsoThumpable") then
             if obj:isDoor() and not obj:isOpen() then
                 if obj:isLocked() then return PathCost.COST_DOOR_LOCKED end
                 cost = cost + PathCost.COST_DOOR_CLOSED
             elseif not obj:isDoor() and not obj:isWindow() and obj:isBlockAllTheSquare() then
                 return PathCost.COST_BLOCKED
             end
        end
        
        -- TREE?
        if instanceof(obj, "IsoTree") then
             -- Trees usually block isFree, but just in case
             -- return PathCost.COST_BLOCKED
        end
    end
    
    -- Hard Walkable check if cost is still low
    -- Note: isFree(false) implies "Not collided".
    if not sq:isFree(false) then
        -- If we added cost for door/window, we might assume we can pass it (by opening/climbing).
        -- If it wasn't a door/window and isFree is false, it's a wall or furniture.
        if cost == PathCost.COST_WALK then
             return PathCost.COST_BLOCKED
        end
    end
    
    -- ZOMBIES
    -- We can check moving objects on the square
    local moving = sq:getMovingObjects()
    for i=0, moving:size()-1 do
       local m = moving:get(i)
       if instanceof(m, "IsoZombie") then
           cost = cost + PathCost.COST_ZOMBIE
       end
    end

    return cost
end

return PathCost
