-- Handler_DebugSpawn.lua
-- Parameters:
--   entity (string): "Vehicle", "Zombie", "Chicken", "Cow", "Pig", "Sheep"
--   count (int): Number to spawn (e.g. 1)

local Handler = {}
local TAG = "[AISurvivorBridge-DebugSpawn] "
-- Safely require util or mock it if missing
local util 
local ok_util, u = pcall(require, "util")
if ok_util then util = u else util = { inspectObject = function() end } end

function Handler.execute(player, params)
    print(TAG .. "Executing spawn command...")
    
    local type = params.entity or "Zombie"
    local count = params.count or 1
    
    local cell = getCell()
    local x = player:getX() + 2
    local y = player:getY() + 2
    local z = player:getZ()
    
    local sq = cell:getGridSquare(x, y, z)
    if not sq then 
        print(TAG .. "Invalid square for spawn.")
        return false 
    end

    if type == "Vehicle" then
        print(TAG .. "Spawning Vehicle...")
        local v = IsoVehicle.new(cell, sq, nil, "Base.CarNormal")
        if v then
             v:setSquare(sq)
             v:addToWorld()
             print(TAG .. "Vehicle Spawned.")
        end

    elseif type == "Zombie" then
        print(TAG .. "Spawning Zombie(s)...")
        addZombiesInOutfit(x, y, z, count, "Generic", 50)
        
    elseif type == "Chicken" or type == "Cow" or type == "Pig" or type == "Sheep" then
        print(TAG .. "Spawning Animal: " .. type)
        
        -- Special probe logic for Chicken investigation
        if type == "Chicken" then
            print(TAG.."Attempting to spawn Animal: " .. type)
            
            -- Strategy 1: AnimalPopulationManager
            local APM = AnimalPopulationManager and AnimalPopulationManager.instance
            if APM then
                -- Try spawnAnimal
                local ok, res = pcall(function() return APM:spawnAnimal(type, x, y, z) end)
                if ok then 
                    print(TAG.."APM:spawnAnimal executed successfully.") 
                    return true
                end

                -- Try createAnimal (Manager method)
                local ok2, res2 = pcall(function() return APM:createAnimal(type, x, y, z) end)
                if ok2 then 
                    print(TAG.."APM:createAnimal executed successfully.") 
                    return true
                end
            else
                print(TAG.."AnimalPopulationManager global NOT found.")
            end

            -- Strategy 2: IsoAnimal Constructor
            if IsoAnimal then
                 print(TAG.."Found IsoAnimal class. Attempting constructors...")
                 local animal = nil
                 
                 -- Attempt 1: params(cell) - Matches IsoVehicle pattern
                 local ok_new, res_new = pcall(function() return IsoAnimal.new(getCell()) end)
                 if ok_new then 
                    animal = res_new 
                 else
                     -- Attempt 2: params() - Fallback
                     print(TAG.."Attempt 1 new(cell) failed. Trying new()...")
                     ok_new, res_new = pcall(function() return IsoAnimal.new() end)
                     if ok_new then animal = res_new end
                 end
                 
     if animal then
        print(TAG.."IsoAnimal.new executed. Instance created: " .. tostring(animal))
        
        -- Brute Force Initialization
        -- "setBreed" crashed (nil), so we skip it.
        
        -- method 2: setType (String)
        if animal.setType then
            print(TAG.."Calling setType('"..type.."')...")
            pcall(function() animal:setType(type) end)
        else
            print(TAG.."animal.setType is NIL.")
        end

        -- method 3: onStartup (String)
        if animal.onStartup then
            print(TAG.."Calling onStartup('"..type.."')...")
            pcall(function() animal:onStartup(type) end)
        end

        -- method 4: Attempt visual/sprite setup
        -- Sometimes entities exist but are invisible.
        -- Try inferring sprite from type
        if animal.setSprite then
             print(TAG.."Calling setSprite('Animals_"..type.."')...") -- Guessing prefix
             pcall(function() animal:setSprite("Animals_"..type) end)
        end

        -- Configure Pos
        if animal.setX then animal:setX(x) end
        if animal.setY then animal:setY(y) end
        if animal.setZ then animal:setZ(z) end
        if animal.setDir then animal:setDir(IsoDirections.S) end
        
        -- Add to World & VERIFY
        print(TAG.."Calling addToWorld()...")
        if animal.addToWorld then 
            animal:addToWorld()
        else
            -- Manual fallback
             local sq_target = cell:getGridSquare(x, y, z)
             if sq_target then 
                animal:setSquare(sq_target)
                sq_target:getMovingObjects():add(animal)
             end
        end

        -- Verification Check
        local final_sq = animal:getCurrentSquare()
        if final_sq then
            print(TAG.."Animal thinks it is on square: " .. tostring(final_sq:getX()) .. "," .. tostring(final_sq:getY()))
            if final_sq:getMovingObjects():contains(animal) then
                print(TAG.."SUCCESS: Animal found in square's movingObjects list.")
            else
                print(TAG.."WARNING: Animal NOT found in square's movingObjects list despite addToWorld.")
            end
        else
            print(TAG.."ERROR: Animal has no current square.")
        end
        
        print(TAG.."IsoAnimal initialization flow complete.")
        return true
     else
        print(TAG.."IsoAnimal.new failed all attempts.")
     end
            else
                 print(TAG.."IsoAnimal global NOT found.")
            end
        end

        local fallback = createAnimal
        if fallback then
            fallback(x, y, z, type)
        else
            print(TAG.."Fallback createAnimal API not found (Pre-B42?). Cannot spawn " .. type)
        end

    else
        print(TAG .. "Unknown entity type: " .. type)
    end

    return true
end

return Handler
