-- Handler_MoveTo.lua

local Handler_MoveTo = {}

local function getSquare(x, y, z)
    return getCell():getGridSquare(x, y, z)
end

function Handler_MoveTo.execute(player, params)
    if not params or not params.x or not params.y then
        print("[AISurvivorBridge] MoveTo missing coordinates")
        return false
    end
    
    local z = params.z or 0
    local sq = getSquare(params.x, params.y, z)
    if not sq then
        print("[AISurvivorBridge] MoveTo target square not loaded/invalid: " .. params.x .. "," .. params.y)
        return false
    end

    local mode = "Walk"
    if params.sprinting then mode = "Sprint"
    elseif params.running then mode = "Run" end

    print("[AISurvivorBridge] [BotCommand] Queuing MoveTo ("..mode..") to " .. params.x .. "," .. params.y)
    
    -- Set movement mode
    if params.running then 
        player:setRunning(true) 
    else 
        player:setRunning(false) 
    end
    
    if params.sprinting then 
        player:setSprinting(true) 
    else 
        player:setSprinting(false) 
    end

    -- Use ISWalkToTimedAction. 
    -- Note: Vanilla ISWalkToTimedAction might override run state. 
    -- If it does, we might need a custom action in future iterations.
    local action = ISWalkToTimedAction:new(player, sq)
    ISTimedActionQueue.add(action)
    
    return true
end

print("[AISurvivorBridge] LOAD SUCCESS: Handler_MoveTo.lua")
return Handler_MoveTo
