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
    
    -- 0-1 Normalized Condition
    local cond = 0
    -- Check if method exists before calling
    if item.getConditionMax and item.getCondition then
        local max = item:getConditionMax()
        if max > 0 then
            cond = item:getCondition() / max
        end
    end
    
    local isDamageable = false
    -- Check if method exists
    if item.isDamageable then
        isDamageable = item:isDamageable()
    end

    local d = {
        id = item:getID(),
        type = item:getFullType(), -- Base.Axe
        cat = tostring(item:getCategory()),
        name = item:getName(),
        weight = item:getActualWeight(),
        cond = cond,
        isDamageable = isDamageable
    }

    if instanceof(item, "HandWeapon") then
         d.minDmg = item:getMinDamage()
         d.maxDmg = item:getMaxDamage()
         d.crit = item:getCriticalChance()
    end
    
    return d
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
        p.moodles = {}
        local moodles = player:getMoodles()
        if moodles then
            -- Safe iteration count
            local count = 0
            if moodles.getNumMoodles then 
                 count = moodles:getNumMoodles()
            elseif moodles.size then 
                 count = moodles:size() 
            end

            for i=0, count-1 do
                local level = moodles:getMoodleLevel(i)
                if level > 0 then
                    local typeName = tostring(moodles:getMoodleType(i))
                    local sentiment = 0
                    -- 0=Neutral, 1=Good, 2=Bad (Standard PZ Enum usually)
                    -- Or we can blindly trust the integer
                    if moodles.getGoodBadNeutral then
                        sentiment = moodles:getGoodBadNeutral(i)
                        -- Mapping (Observation required, assuming 1=Good, 2=Bad, 0=Neutral/Info for now)
                        -- Actually standard is: 0=Good, 1=Bad, 2=Neutral ? Or 1=Good, 2=Bad?
                        -- We will pass the raw int and handle visualization in debug_bot
                    end
                    
                    table.insert(p.moodles, {
                        name = typeName,
                        value = level,
                        sentiment = sentiment
                    })
                end
            end
        end

        -- === INVENTORY ===
        -- Flattened list for bot simplicity
        p.inventory = {}
        
        local function processItem(item, list)
            local d = getItemData(item)
            if not d then return end
            
            -- Check for nested items (Bag, KeyRing, etc.)
            if item.getInventory then
                local inv = item:getInventory()
                if inv and not inv:isEmpty() then
                    d.items = {}
                    local subItems = inv:getItems()
                    for j=0, subItems:size()-1 do
                        local sub = subItems:get(j)
                        -- Recursive call
                        processItem(sub, d.items)
                    end
                end
            end
            
            table.insert(list, d)
        end

        local inv = player:getInventory()
        -- 1. Main Inventory
        local items = inv:getItems()
        for i=0, items:size()-1 do
             processItem(items:get(i), p.inventory)
        end
        
        -- 2. Equipped (Primary/Secondary) - Add only if NOT already in main (usually are in main too?)
        -- In PZ, equipped items are in inventory. Sticky situation.
        -- Just relying on main inventory listing is usually enough.
        -- We can mark them as equipped if needed.
        
        -- Mark timestamp for debugging
        p.inventory_timestamp = now
        
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