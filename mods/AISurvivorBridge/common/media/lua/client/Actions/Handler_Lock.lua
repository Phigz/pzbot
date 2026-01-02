-- Handler_Lock.lua
local Handler_Lock = {}
local TAG = "[Action-Lock] "

-- Require Actions
if not ISLockDoor then require "TimedActions/ISLockDoor" end
if not ISOpenDoorToAction then require "TimedActions/ISOpenDoorToAction" end
if not ISOpenCloseDoor then require "TimedActions/ISOpenCloseDoor" end

-- Helpers
local function getSquare(x, y, z)
    local cell = getCell()
    if not cell then return nil end
    return cell:getGridSquare(x, y, z)
end

local function findObjectById(idString)
    -- Simplified for brevity, matching Handler_Interact logic
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

function Handler_Lock.execute(player, params)
    local targetId = params.targetId
    if not targetId then return false end
    
    local obj = findObjectById(targetId)
    if not obj then return false end

    if instanceof(obj, "IsoDoor") then
        print(TAG .. "Locking Door")
        
        -- 1. Walk to door
        ISTimedActionQueue.add(ISWalkToTimedAction:new(player, obj:getSquare()))

        -- 2. Ensure Closed
        if obj:IsOpen() then
             print(TAG .. "Door is open, closing first...")
             -- Re-use ISOpenDoorToAction if available, else ISOpenCloseDoor
             if ISOpenDoorToAction then
                 ISTimedActionQueue.add(ISOpenDoorToAction:new(player, obj))
             elseif ISOpenCloseDoor then
                 ISTimedActionQueue.add(ISOpenCloseDoor:new(player, obj, false)) -- false=close
             end
        end

        -- 3. Lock
        if ISLockDoor then
            ISTimedActionQueue.add(ISLockDoor:new(player, obj, true)) -- true = lock
            return true
        else
            print(TAG .. "ISLockDoor class not found")
        end
    end

    print(TAG .. "Cannot lock this object: " .. tostring(obj))
    return false
end

return Handler_Lock
