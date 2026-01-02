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
        


        -- Temperature: Use v42 Thermoregulator API
        local temp = 37.0
        if bodyDamage.getThermoregulator then
             local thermo = bodyDamage:getThermoregulator()
             if thermo and thermo.getCoreTemperature then
                 temp = thermo:getCoreTemperature()
             end
        end

        -- === STATS & NUTRITION ===
        local stats = nil
        if player.getStats then stats = player:getStats() end
        
        local nutrition = nil
        if player.getNutrition then nutrition = player:getNutrition() end


        
        -- Safe Extraction Helpers
        -- Tries: 1. getMethod(), 2. field
        local function getStat(obj, propName)
            if not obj then return 0.0 end
            
            -- 1. Try Method: getPropName() (e.g. getFatigue)
            local method = "get" .. string.upper(string.sub(propName, 1, 1)) .. string.sub(propName, 2)
            if obj[method] then return obj[method](obj) end
            
            -- 2. Try Field: propName (e.g. fatigue)
            if obj[propName] then return obj[propName] end
            
            return 0.0
        end

        -- Dump Stats to string once per update to parse fields
        -- (Since direct access to Stats fields fails in Kahlua for this object)
        local statsStr = ""
        if stats then statsStr = tostring(stats) end
        
        -- Extraction Helper: Parse from String Dump
        -- Output format: "Stats{ ... Fatigue = 0.0 ... }"
        local function getVal(propName)
             -- 1. Try direct map (Performance)
             -- (If successful in future, we can skip search)
             
             -- 2. Parse from String
             -- Capitalize first letter: fatigue -> Fatigue
             local capProp = string.upper(string.sub(propName, 1, 1)) .. string.sub(propName, 2)
             
             -- Pattern: "Key = Value"
             -- We look for "Fatigue = 0.123"
             local pattern = capProp .. "%s*=%s*([%d%.E%-]+)"
             local match = string.match(statsStr, pattern)
             
             if match then
                 return tonumber(match)
             end
             
             return 0.0
        end

        p.body = {
            health = bodyDamage:getOverallBodyHealth(), 
            temperature = temp,
            
            -- Vitals parsed from string dump
            fatigue = getVal("fatigue"),
            endurance = getVal("endurance"),
            hunger = getVal("hunger"),
            thirst = getVal("thirst"),
            stress = getVal("stress"),
            panic = getVal("panic"),
            sanity = getVal("sanity"),
            boredom = getVal("boredom"),
            
            nutrition = {
                calories = getStat(nutrition, "calories"),
                weight = getStat(nutrition, "weight"),
                carbohydrates = getStat(nutrition, "carbohydrates"),
                proteins = getStat(nutrition, "proteins"),
                lipids = getStat(nutrition, "lipids")
            },

            parts = {}
        }
        

        -- === MOODLES === 
        p.moodles = {}
        local moodles = player:getMoodles()
        local MT = MoodleType -- Confirmed Global text
        
        if moodles and MT then
             -- Dynamic Iteration: Use the keys found in MoodleType
             for key, val in pairs(MT) do
                 -- Filter: Look for UPPERCASE keys that aren't system fields
                 if type(key) == "string" and key == string.upper(key) and string.len(key) > 1 then
                     
                     local ok, level = pcall(function() return moodles:getMoodleLevel(val) end)
                     
                     if ok and level and level > 0 then
                        -- Format Name: TRIED -> Tired, HAS_A_COLD -> HasACold
                        local name = key:lower()
                        -- Remove underscores and capitalize next letter
                        name = name:gsub("_(%l)", function(c) return c:upper() end)
                        -- Capitalize first letter
                        name = name:gsub("^%l", string.upper)
                        
                        -- Sentiment Mapping (-1=Bad, 1=Good, 0=Neutral)
                        local sentimentMap = {
                            ENDURANCE = -1,
                            TIRED = -1,
                            HUNGRY = -1,
                            PANIC = -1,
                            SICK = -1,
                            BORED = -1,
                            UNHAPPY = -1,
                            BLEEDING = -1,
                            WET = -1,
                            HAS_A_COLD = -1,
                            ANGRY = -1,
                            STRESS = -1,
                            THIRST = -1,
                            INJURED = -1,
                            PAIN = -1,
                            HEAVY_LOAD = -1,
                            DRUNK = -1,
                            DEAD = -1,
                            ZOMBIE = -1,
                            HYPERTHERMIA = -1,
                            HYPOTHERMIA = -1,
                            WINDCHILL = -1,
                            CANT_SPRINT = -1,
                            UNCOMFORTABLE = -1,
                            NOXIOUS_SMELL = -1,
                            FOOD_EATEN = 1
                        }
                        
                        local sentiment = sentimentMap[key] or 0
                        
                        table.insert(p.moodles, { 
                           name = name, 
                           value = level, 
                           sentiment = sentiment 
                        })
                     end
                 end
             end
        end
        
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

        -- === ENVIRONMENT ===
        local gt = getGameTime()
        local clim = getClimateManager()
        
        -- Light Level (Approx from player square)
        local light = 0.0
        local pSq = getPlayer():getCurrentSquare()
        if pSq then
             light = pSq:getLightLevel(0) -- viewport 0
        end

        local clouds = clim:getCloudIntensity()
        local weatherStr = "Clear"
        
        if clim:getRainIntensity() > 0.5 then weatherStr = "Storm"
        elseif clim:getRainIntensity() > 0.0 then weatherStr = "Raining"
        elseif clim:getFogIntensity() > 0.25 then weatherStr = "Foggy"
        elseif clouds > 0.6 then weatherStr = "Overcast"
        elseif clouds > 0.25 then weatherStr = "Cloudy"
        end

        state.environment = {
            time_of_day = gt:getTimeOfDay(),
            rain = clim:getRainIntensity(),
            fog = clim:getFogIntensity(),
            clouds = clouds,
            temperature = clim:getAirTemperatureForCharacter(getPlayer()), 
            wind_speed = clim:getWindIntensity(),
            light_level = light,
            ex_temp = clim:getTemperature(), -- Global Air Temp
            weather = weatherStr 
        }

        -- Write to disk
        util.writeState(OUTPUT_FILE_NAME, state)
    end
end

-- Events
Events.OnGameStart.Add(ObservationClient.OnGameStart)
Events.OnPlayerUpdate.Add(ObservationClient.OnPlayerUpdateObserve)

print(TAG.."ObservationClient.lua loaded!")
return ObservationClient