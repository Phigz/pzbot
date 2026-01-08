DirectControl = {}
DirectControl.targetVector = {x=0, y=0}
DirectControl.isActive = false
DirectControl.lastUpdate = 0
DirectControl.TIMEOUT_MS = 500

-- Java Imports
local Vector2 = zombie.iso.Vector2
local moveVec = Vector2.new(0, 0)

function DirectControl.setVector(x, y)
    DirectControl.targetVector.x = x
    DirectControl.targetVector.y = y
    DirectControl.isActive = true
    DirectControl.lastUpdate = getTimeInMillis()
    -- print(string.format("[DirectControl] Set Vector: %.2f, %.2f", x, y))
end

function DirectControl.onTick()
    if not DirectControl.isActive then return end
    
    local player = getSpecificPlayer(0)
    if not player then return end

    -- Timeout logic
    if getTimeInMillis() - DirectControl.lastUpdate > DirectControl.TIMEOUT_MS then
        DirectControl.isActive = false
        DirectControl.targetVector = {x=0, y=0}
        -- Clear movement?
        player:setMoveDelta(0)
        return
    end
    
    local dx = DirectControl.targetVector.x
    local dy = DirectControl.targetVector.y
    
    -- Apply Movement directly
    -- Apply Movement (Physics)
    if math.abs(dx) > 0.01 or math.abs(dy) > 0.01 then
        moveVec:set(dx, dy)
        moveVec:setLength(0.06) -- Walking Speed (~3.6 tiles/sec)
        
        -- Rotate (Analog Steering)
        player:setForwardDirection(moveVec)
        
        -- Apply Physics (Displacement)
        player:Move(moveVec)
        
        -- Sync Render Position
        pcall(player.setLx, player, player:getX())
        pcall(player.setLy, player, player:getY())
        pcall(player.setLz, player, player:getZ())
        
        -- Force Animation State
        player:setMoveDelta(1.0)
        -- Try String values for Kahlua/Java interop
        player:setVariable("Walking", "true") 
        player:setVariable("WalkSpeed", "1.0")
        
        -- Try Forcing Run (Jog) - maybe easier to trigger?
        player:setForceRun(true)
        player:setRunning(true)
    else
        player:setMoveDelta(0)
        player:setVariable("Walking", "false")
        player:setForceRun(false)
        player:setRunning(false)
    end
end

Events.OnPlayerUpdate.Add(DirectControl.onTick)
