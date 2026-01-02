-- Handler_Interact.lua
-- Handles generic "Interact" commands (Doors, Lights, etc.)

local Handler_Interact = {}
local TAG = "[Action-Interact] "

-- Ensure TimedActions are loaded
-- Ensure TimedActions are loaded
if not ISOpenDoorToAction then 
    print(TAG.."Requiring ISOpenDoorToAction...")
    require "TimedActions/ISOpenDoorToAction" 
end
if not ISOpenDoorToAction then
    print(TAG.."WARNING: ISOpenDoorToAction is still nil! Trying ISOpenCloseDoor...")
    if not ISOpenCloseDoor then require "TimedActions/ISOpenCloseDoor" end
    -- Fallback mapping if needed, or handle in execute
end

if not ISToggleLightAction then require "TimedActions/ISToggleLightAction" end
if not ISOpenCloseWindow then require "TimedActions/ISOpenCloseWindow" end
if not ISOpenCloseCurtain then require "TimedActions/ISOpenCloseCurtain" end

local function getSquare(x, y, z)
    local cell = getCell()
    if not cell then return nil end
    return cell:getGridSquare(x, y, z)
end

-- Smart Navigation Helper
-- Returns the best square to stand on to interact with 'obj'
-- 1. Identify valid interaction positions (adjacent squares)
-- 2. Pick the one closest to player (Pathfinding distance preferred, but Euclidean ok for now)
local function getBestInteractSquare(player, obj)
    local pSq = player:getCurrentSquare()
    local oSq = obj:getSquare()
    
    if not oSq or not pSq then return nil end
    
    -- If we are already adjacent (distance <= 1.5ish), just use current square?
    -- Windows specifically need `IsoWindow:getActionableSquare?` No, that's internal.
    
    -- For Windows/Doors:
    -- Usually 2 valid squares: Inside and Outside.
    -- We want the one closest to us.
    
    if instanceof(obj, "IsoWindow") or instanceof(obj, "IsoDoor") then
        local north = obj:getNorth() -- Boolean
        local x, y, z = oSq:getX(), oSq:getY(), oSq:getZ()
        
        -- Candidates
        local sq1, sq2
        if north then
            -- Door/Window runs along X axis (North wall of a cell?) No, North=True means facing North?
            -- Actually North property on object usually means "Is this object on the North edge of the tile?"
            -- If North=True: It separates (x,y) and (x,y-1).
            sq1 = oSq -- The tile the object is on
            sq2 = getSquare(x, y-1, z) -- The tile "behind" it (North)
        else
            -- West edge?
            -- If North=False: It separates (x,y) and (x-1,y).
            sq1 = oSq
            sq2 = getSquare(x-1, y, z) -- The tile "west" of it
        end
        
        -- Fallback if sq2 nil
        if not sq2 then return sq1 end
        
        -- Evaluate Distance
        local d1 = sq1:DistTo(player)
        local d2 = sq2:DistTo(player)
        
        -- Prefer the closer one.
        if d1 < d2 then return sq1 else return sq2 end
    end
    
    -- Default for others (Light, etc): Just the object's square
    return oSq
end

-- Helper: Locate Object by synthetic ID (int_x_y_i or x_y_i)
local function findObjectById(idString)
    if not idString then return nil end

    -- 1. Try Coordinate ID
    -- Pattern: int_X_Y_Z or X_Y_Z (Sensor.lua uses both... strictly X_Y_I)
    local x, y, i = string.match(idString, "int_(%d+)_(%d+)_(%d+)")
    if not x then x, y, i = string.match(idString, "(%d+)_(%d+)_(%d+)") end

    if x and y and i then
        local sq = getSquare(tonumber(x), tonumber(y), 0) -- Assuming Z=0 for now, need to encode Z in ID?
        -- Sensor.lua ID is x_y_i. Does 'i' include objects list? Yes.
        -- But Sensor.lua uses `obj:getZ()` so Z is implicit in the object location, but not the ID?
        -- Wait, ID generation in Sensor line 81: "int_"..x.."_"..y.."_"..i
        -- Line 642: x.."_"..y.."_"..i.
        -- Neither has Z. This is a flaw in Sensor.lua if Z != 0.
        
        if sq then
             local objects = sq:getObjects()
             local idx = tonumber(i)
             if objects and idx < objects:size() then
                 return objects:get(idx)
             end
        end
    end

    -- 2. Try Global ID (for MovingObjects)
    -- If it's just a number string
    -- But Interact is usually for Static objects. MovingObjects use numeric ID.
    -- Let's try to match numeric.
    local numId = tonumber(idString)
    if numId then
         -- Would need to scan cell object list. Expensive?
         -- But MovingObjects usually targeted by Attack/Follow, not Interact (unless looting corpse).
    end

    return nil
end

function Handler_Interact.execute(player, params)
    local targetId = params.targetId
    if not targetId then
        print(TAG .. "Available params: " .. tostring(params))
        print(TAG .. "Error: Missing targetId")
        return false 
    end

    local obj = findObjectById(targetId)
    if not obj then
        print(TAG .. "Target object not found: " .. tostring(targetId))
        return false
    end

    -- Dispatch Helper
    local queue = ISTimedActionQueue.add
    
    -- 1. DOORS
    if instanceof(obj, "IsoDoor") then
        print(TAG .. "Interacting with Door")
        
        -- Force Walk to square (adjacent or same)
        -- Using getSquare() might put us ON the door, which is okay for opening, 
        -- but usually we want to be adjacent. ISWalkToTimedAction logic usually handles "path to adjacent".
        -- Let's just walk to the door's square.
        ISTimedActionQueue.add(ISWalkToTimedAction:new(player, obj:getSquare()))

        if ISOpenDoorToAction then
            queue(ISOpenDoorToAction:new(player, obj))
        elseif ISOpenCloseDoor then
             print(TAG .. "Falling back to ISOpenCloseDoor")
             queue(ISOpenCloseDoor:new(player, obj, not obj:IsOpen()))
        else
            print(TAG .. "ERROR: No Door Action Classes found!")
        end
        return true
    end

    -- 2. WINDOWS
    if instanceof(obj, "IsoWindow") then
        print(TAG .. "Interacting with Window")
        local targetSq = getBestInteractSquare(player, obj)
        ISTimedActionQueue.add(ISWalkToTimedAction:new(player, targetSq))
        queue(ISOpenCloseWindow:new(player, obj, 50))
        return true
    end

    -- 3. LIGHT SWITCH
    if instanceof(obj, "IsoLightSwitch") then
        print(TAG .. "Toggling Light")
        ISTimedActionQueue.add(ISWalkToTimedAction:new(player, obj:getSquare())) -- Lights logic is safe usually
        ISTimedActionQueue.add(ISToggleLightAction:new(player, obj))
        return true
    end
    
    -- 4. CURTAINS
    if instanceof(obj, "IsoCurtain") then
        print(TAG .. "Interacting with Curtain")
        -- Curtains are on windows/doors, so use smart logic
        -- But Curtain object might not have getNorth? It's usually attached to object.
        -- Let's check parent? 
        local targetSq = obj:getSquare()
        -- Determine window
        -- obj:getObjectAllowed? 
        -- Fallback to basic square if smart logic fails.
        ISTimedActionQueue.add(ISWalkToTimedAction:new(player, targetSq))
        queue(ISOpenCloseCurtain:new(player, obj, 50))
        return true
    end

    -- 5. GENERIC THUMPABLE
    if instanceof(obj, "IsoThumpable") and obj:isDoor() then
         print(TAG .. "Interacting with Thumpable Door")
         -- Thumpables might behave like doors
         local targetSq = getBestInteractSquare(player, obj)
         ISTimedActionQueue.add(ISWalkToTimedAction:new(player, targetSq))
         queue(ISOpenDoorToAction:new(player, obj))
         return true
    end
    
    -- 6. STOVES (New)
    if instanceof(obj, "IsoStove") or instanceof(obj, "IsoFireplace") then
         print(TAG .. "Interacting with Stove")
         ISTimedActionQueue.add(ISWalkToTimedAction:new(player, obj:getSquare()))
         ISTimedActionQueue.add(ISToggleLightAction:new(player, obj)) 
         return true
    end

    print(TAG .. "Unhandled object type: " .. tostring(obj:getClass():getSimpleName()))
    return false
end

return Handler_Interact
