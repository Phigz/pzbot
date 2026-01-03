-- Navigation/Navigator.lua
-- Handles movement using Project Zomboid's built-in ISTimedActionQueue system
local Navigator = {}

-- PZ Standard Libraries
-- ISWalkToTimedAction is global, no require needed usually.
-- ISTimedActionQueue is global.

local TAG = "[Navigator] "

function Navigator.moveTo(player, x, y, z, stance)
    local tx, ty = math.floor(x), math.floor(y)
    local z = z or player:getZ()
    print(TAG .. "Request MoveTo (ActionQueue): " .. tx .. "," .. ty)
    
    local targetSq = getCell():getGridSquare(tx, ty, z)
    
    if not targetSq then
        print(TAG .. "Target square not loaded: " .. tx .. "," .. ty)
        -- Attempt to move related to world coordinates if possible, but ISWalkTo needs a square.
        -- Fallback: Use adjacent loaded square?
        return
    end
    
    -- Verify dependencies (using correct class name from Probe)
    if not ISWalkToTimedAction or not ISTimedActionQueue then
        print(TAG .. "CRITICAL ERROR: ISWalkToTimedAction or ISTimedActionQueue not found.")
        print(TAG .. "ISWalkToTimedAction: " .. tostring(ISWalkToTimedAction))
        print(TAG .. "ISTimedActionQueue: " .. tostring(ISTimedActionQueue))
        return
    end

    -- Clear previous actions (interrupt current movement)
    ISTimedActionQueue.clear(player)
    
    -- Create the Walk Action
    -- ISWalkToTimedAction:new(character, targetSquare)
    local action = ISWalkToTimedAction:new(player, targetSq)
    
    if not action then
        print(TAG .. "Failed to create ISWalkToTimedAction.")
        return
    end
    
    -- Optional: Configure the action (running, etc.)
    -- Handle Stance (Speed)
    player:setRunning(false)
    player:setSneaking(false)
    -- player:setSprinting(false) -- Check if exists? Safe to call if nil? escaping for now.
    
    if stance == "Run" then
        player:setRunning(true)
    elseif stance == "Sprint" then
        player:setRunning(true) 
        -- Attempt Sprint (Requires endurance/shoes usually)
        if player.setSprinting then player:setSprinting(true) end
    elseif stance == "Sneak" then
        player:setSneaking(true)
    end
    
    -- Handle Aiming
    -- Passed via optional arg or encoded in stance? 
    -- Let's check if 'aiming' was passed. 
    -- For now, we rely on the implementation to set Navigator.aiming based on calling args, 
    -- but moveTo signature is (player, x, y, z, stance).
    -- We can overload 'stance' or add a global 'Navigator.isAiming'.
    -- Or better: Parse stance for "Aim" prefix? e.g. "AimWalk", "AimRun"?
    
    -- Let's support "Aim" as a stance, or combined.
    -- Better: allow `stance` to be a table? No, kept simple.
    -- If stance is "Aim", we Walk + Aim.
    if stance == "Aim" then
         player:setIsAiming(true)
         -- Aiming implies walking usually
    end

    action.setOnComplete = function()
        print(TAG .. "ISWalkToTimedAction Completed.")
        Navigator.isMoving = false
        player:setRunning(false)
        player:setSneaking(false)
        player:setIsAiming(false)
        if player.setSprinting then player:setSprinting(false) end
    end

    -- Add to Queue
    print(TAG .. "Adding WalkTo action to queue. Stance: " .. tostring(stance))
    ISTimedActionQueue.add(action)
    
    -- Set flag for update loop (visuals only)
    Navigator.isMoving = true
    Navigator.currentStance = stance 
end

function Navigator.stop(player)
    print(TAG .. "Stopping.")
    if ISTimedActionQueue then
        ISTimedActionQueue.clear(player)
    end
    player:setMoveDelta(0)
    player:setRunning(false)
    player:setSneaking(false)
    player:setIsAiming(false)
    if player.setSprinting then player:setSprinting(false) end
    Navigator.isMoving = false
end

function Navigator.update(player)
    -- Monitor the Action Queue (Simplified)
    
    if Navigator.isMoving then
        -- Enforce Stance Persistence (ISWalkToTimedAction resets these often)
        if Navigator.currentStance == "Run" then
             player:setRunning(true)
        elseif Navigator.currentStance == "Sprint" then
             player:setRunning(true)
             if player.setSprinting then player:setSprinting(true) end
        elseif Navigator.currentStance == "Sneak" then
             player:setSneaking(true)
        elseif Navigator.currentStance == "Aim" then
             player:setIsAiming(true)
             player:setRunning(false) -- Aiming forces walk
        end
    end
end

return Navigator
