-- ObservationClient.lua
local util = require("util")
local Sensor = require("Sensor")


local TAG = "[AISurvivorBridge] "
local OUTPUT_FILE_NAME = "AISurvivorBridge/state.json"

print(TAG.."ObservationClient.lua loading..")
local ObservationClient = {}

local lastStateWriteTime = 0
local WRITE_INTERVAL_MS = 200

local lastScanTime = 0
local SCAN_INTERVAL_MS = 100

-- Global state object for this module
local state = nil

-- Helper to structure item data
local function getItemData(item)
    if not item then return nil end
    return {
        id = item:getID(),
        type = item:getFullType(), -- Base.Axe
        cat = tostring(item:getCategory()),
        name = item:getName(),
        weight = item:getActualWeight(),
        cond = item:getCondition() / item:getConditionMax() -- Normalized 0-1
    }
end

function ObservationClient.OnGameStart()
    print(TAG.."Initializing ObservationClient State...")
    state = util.initState()
    util.writeState(OUTPUT_FILE_NAME, state)
end

function ObservationClient.OnPlayerUpdateObserve(player)
    if not player or player:isDead() then return end
    if not state then state = util.initState() end -- Safety init

    local now = getTimestampMs()
    
    -- === DEBUG: Inspect Moodles (Run Once) ===
    if not _G.api_v42_inspected_moodles then
        print("[INSPECT] Investigating Moodle API...")
        local moods = player:getMoodles()
        print("[INSPECT] player:getMoodles() -> " .. tostring(moods))
        if moods then
            util.inspectObject(moods, nil) -- Inspect ALL methods on the moodle object
        end
        _G.api_v42_inspected_moodles = true
    end

    -- 1. Vision Scan (Throttled)
    if (now - lastScanTime) > SCAN_INTERVAL_MS then
        state.player.vision = Sensor.scan(player, 15)
        lastScanTime = now
    end

    -- 2. State Update & Write (Throttled)
    if (now - lastStateWriteTime) > WRITE_INTERVAL_MS then
        lastStateWriteTime = now
        
        state.timestamp = now
        state.tick = getGameTime():getWorldAgeHours()

        local p = state.player
        
        -- === POSITION ===
        p.position.x = player:getX()
        p.position.y = player:getY()
        p.position.z = player:getZ()
        p.rotation = player:getDirectionAngle()

        -- === STATE FLAGS ===
        p.state = {
            aiming = player:isAiming(),
            sneaking = player:isSneaking(),
            running = player:isRunning(),
            sprinting = player:isSprinting(),
            in_vehicle = player:isSeatedInVehicle(),
            is_sitting = player:isSitOnGround()
        }

        local bodyDamage = player:getBodyDamage()
        
        -- DEBUG: Inspect BodyDamage & Thermoregulator (Run Once)
        if not _G.api_v42_inspected_bodydamage then
             print("[INSPECT] Investigating BodyDamage API...")
             util.inspectObject(bodyDamage, nil)
             
             if bodyDamage.getThermoregulator then
                 print("[INSPECT] Investigating Thermoregulator API...")
                 util.inspectObject(bodyDamage:getThermoregulator(), nil)
             end
             _G.api_v42_inspected_bodydamage = true
        end

        -- Temperature: Use v42 Thermoregulator API
        local temp = 37.0
        if bodyDamage.getThermoregulator then
             local thermo = bodyDamage:getThermoregulator()
             if thermo and thermo.getCoreTemperature then
                 temp = thermo:getCoreTemperature()
             end
        end

        p.body = {
            health = bodyDamage:getOverallBodyHealth(), 
            temperature = temp,
            parts = {}
        }
        
        local bodyParts = bodyDamage:getBodyParts()
        
        for i=0, bodyParts:size()-1 do
            local part = bodyParts:get(i)
            local typeName = tostring(part:getType())
            
            p.body.parts[typeName] = {
                -- Base Health
                health = part:getHealth(),
                bandaged = part:bandaged(),
                bleeding = part:bleeding(),
                bitten = part:bitten(),
                scratched = part:scratched(),
                
                -- Advanced Medical
                pain = part:getPain(),
                burn = part:getBurnTime() > 0,
                fracture = part:getFractureTime() > 0,
                deep_wound = part:isDeepWounded(),
                glass = part:haveGlass(),
                bullet = part:haveBullet(),
                infection = part:getWoundInfectionLevel(),
                splinted = part:isSplint(), -- Fixed in v42
                stitch = part:getStitchTime() > 0
            }
        end

        -- === MOODLES === 
        -- Probe for Moodle API (Run Once)
        if not _G.api_v42_probed_moodles then
             print("[INSPECT] Probing Moodle API...")
             local moods = player:getMoodles()
             if moods then
                 local candidates = {"getNumMoodles", "size", "getMoodleLevel", "getMoodleType", "getGoodBadNeutral", "getDisplayName"}
                 for _, method in ipairs(candidates) do
                     if moods[method] then
                          print("[INSPECT] Found Moodle Candidate: " .. method)
                          -- Try calling simple getters
                          if method == "getNumMoodles" or method == "size" then
                               local status, res = pcall(moods[method], moods)
                               print("[INSPECT] Call " .. method .. " -> " .. tostring(status) .. " : " .. tostring(res))
                          end
                     end
                 end
             end
             _G.api_v42_probed_moodles = true
        end
        
        p.moodles = {}
        -- Placeholder until probe confirms iteration method
        -- local moods = player:getMoodles()
        -- for i=0, moods:getNumMoodles()-1 do ...
        --     local level = moods:getMoodleLevel(i)
        --     if level > 0 then
        --         local typeName = tostring(moods:getMoodleType(i))
        --         p.moodles[typeName] = level
        --     end
        -- end

        -- === INVENTORY ===
        local inv = player:getInventory()
        p.inventory = {
            held = {
                primary = getItemData(player:getPrimaryHandItem()),
                secondary = getItemData(player:getSecondaryHandItem())
            },
            worn = {},
            main = {}
        }

        -- Worn Items (Restored for v42)
        local wornItems = player:getWornItems()
        if wornItems then
            for i=0, wornItems:size()-1 do
                local worn = wornItems:getItemByIndex(i)
                local fullType = tostring(worn:getFullType())
                
                -- Filter out v42 visual wounds (they appear as clothing)
                if not string.find(fullType, "Wound_") then
                    table.insert(p.inventory.worn, getItemData(worn))
                end
            end
        end

        -- Main Inventory Content
        local items = inv:getItems()
        for i=0, items:size()-1 do
            local item = items:get(i)
            table.insert(p.inventory.main, getItemData(item))
        end
        
        -- === ACTION STATE ===
        local ActionClient = _G.AISurvivorBridge_ActionClient
        local actionStatus = nil
        
        if Config and Config.EnableActionSystem and ActionClient then
             actionStatus = ActionClient.getStatus(player)
        elseif ActionClient then
             -- Fallback if Config not loaded yet
             actionStatus = ActionClient.getStatus(player)
        end
        
        if actionStatus then
            p.action_state.status = actionStatus.status
            p.action_state.sequence_number = actionStatus.sequence_number
            p.action_state.queue_busy = actionStatus.queue_busy
            p.action_state.current_action_id = actionStatus.current_action_id
            p.action_state.current_action_type = actionStatus.current_action_type
        end

        -- Write to disk
        util.writeState(OUTPUT_FILE_NAME, state)
    end
end

-- Events
Events.OnGameStart.Add(ObservationClient.OnGameStart)
Events.OnPlayerUpdate.Add(ObservationClient.OnPlayerUpdateObserve)

print(TAG.."ObservationClient.lua loaded!")
return ObservationClient