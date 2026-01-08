-- Handler_Unlock.lua
local Handler_Unlock = {}
local TAG = "[Action-Unlock] "

-- Require Actions
if not ISUnlockDoor then require "TimedActions/ISUnlockDoor" end

local function getSquare(x, y, z)
    local cell = getCell()
    if not cell then return nil end
    return cell:getGridSquare(x, y, z)
end

local function findObjectById(idString)
    local x, y, i = string.match(idString, "int_(%d+)_(%d+)_(%d+)")
    if not x then x, y, i = string.match(idString, "(%d+)_(%d+)_(%d+)") end
    if x and y and i then
        local sq = getSquare(tonumber(x), tonumber(y), 0)
        if sq then
             local objects = sq:getObjects()
             local idx = tonumber(i)
             if objects and idx < objects:size() then return objects:get(idx) end
        end
    end
    return nil
end

function Handler_Unlock.execute(player, params)
    local targetId = params.targetId
    if not targetId then return false end
    
    local obj = findObjectById(targetId)
    if not obj then return false end

    if instanceof(obj, "IsoDoor") then
        print(TAG .. "Unlocking Door")
        if ISUnlockDoor then
            -- Queue walk to the door first
            ISTimedActionQueue.add(ISWalkToTimedAction:new(player, obj:getSquare()))
            -- Then queue the unlock action
            -- ISUnlockDoor:new(character, door)
            ISTimedActionQueue.add(ISUnlockDoor:new(player, obj))
            return true
        else
            print(TAG .. "ISUnlockDoor class not found")
        end
    end

    print(TAG .. "Cannot unlock this object: " .. tostring(obj))
    return false
end

return Handler_Unlock
