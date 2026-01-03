-- Handler_MoveTo.lua

local Handler_MoveTo = {}

local function getSquare(x, y, z)
    return getCell():getGridSquare(x, y, z)
end

local Navigator = require "Navigation/Navigator"

function Handler_MoveTo.execute(player, params)
    if not params or not params.x or not params.y then
        print("[AISurvivorBridge] MoveTo missing coordinates")
        return false
    end
    
    local z = params.z or 0
    local targetStance = "Auto"
    if params.stance then targetStance = params.stance
    elseif params.sprinting then targetStance = "Sprint"
    elseif params.running then targetStance = "Run" 
    end

    print("[AISurvivorBridge] [BotCommand] Navigator MoveTo ("..targetStance..") to " .. params.x .. "," .. params.y)
    
    -- Check distance?
    local dist = math.sqrt(math.pow(params.x - player:getX(), 2) + math.pow(params.y - player:getY(), 2))
    if dist < 0.5 then
        print("[AISurvivorBridge] Already close to target. Skipping.")
        return true
    end

    -- Call Navigator
    Navigator.moveTo(player, params.x, params.y, z, targetStance)
    
    -- Navigator.moveTo starts the movement immediately.
    -- ActionClient now tracks Navigator.isMoving directly, so we don't need a blocking TimedAction.
    return true
end

print("[AISurvivorBridge] LOAD SUCCESS: Handler_MoveTo.lua")
return Handler_MoveTo
