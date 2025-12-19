-- Handler_Pathfind.lua

local Handler_Pathfind = {}

local function getSquare(x, y, z)
    return getCell():getGridSquare(x, y, z)
end

function Handler_Pathfind.execute(player, params)
    if not params or not params.x or not params.y then
        print("[AISurvivorBridge] Pathfind missing coordinates")
        return false
    end
    
    local z = params.z or 0
    local sq = getSquare(params.x, params.y, z)
    if not sq then
        -- Attempt to fetch square if not loaded? 
        -- ISWalkToTimedAction usually requires a loaded square object.
        print("[AISurvivorBridge] Pathfind target square not loaded/invalid: " .. params.x .. "," .. params.y)
        return false
    end

    print("[AISurvivorBridge] [BotCommand] Queuing Pathfind to " .. params.x .. "," .. params.y)
    ISTimedActionQueue.add(ISWalkToTimedAction:new(player, sq))
    return true
end

return Handler_Pathfind
