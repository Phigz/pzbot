-- Handler_Attack.lua
-- Handles "Attack" commands (Swing weapon at target)

local Handler_Attack = {}
local TAG = "[Action-Attack] "

local function findTargetById(idString)
    if not idString then return nil end
    local cell = getCell()
    if not cell then return nil end
    
    local list = cell:getObjectList()
    if not list then return nil end
    
    local idNum = tonumber(idString)
    
    for i=0, list:size()-1 do
        local obj = list:get(i)
        if obj and instanceof(obj, "IsoMovingObject") then
             -- String match to be safe against float/int diffs
             if tostring(obj:getID()) == idString then
                 return obj
             end
             -- Fallback for int comparison
             if idNum and obj:getID() == idNum then
                 return obj
             end
        end
    end
    return nil
end

function Handler_Attack.execute(player, params)
    local targetId = params.targetId
    if not targetId then
        print(TAG .. "Error: Missing targetId")
        return false 
    end

    local target = findTargetById(targetId)
    if not target then
        print(TAG .. "Target not found: " .. tostring(targetId))
        return false
    end

    print(TAG .. "Attacking Target: " .. tostring(target))

    -- 1. Face the target
    player:faceThisObject(target)
    
    -- 2. Execute Attack
    -- Direct API call to trigger swing mechanism
    -- AttemptAttack(float charge)
    player:AttemptAttack(0.5) 
    
    -- Note: This is an instant action, not a TimedAction.
    -- To play nice with queue, we typically want a TimedAction wrapper.
    -- For now, this effectively "interrupts" or runs alongside.
    -- Ideally we insert a "ISWait" or dummy action to block queue?
    
    return true
end

return Handler_Attack
