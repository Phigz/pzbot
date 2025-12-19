-- util.lua
local json = require("json")

local util = {}

local TAG = "[AISurvivorBridge] "
print(TAG.."util.lua loading..")

-- encode
local encode = function(state)
    local ok, jsonText = pcall(json.encode, state)
    if not ok then
        print(TAG.."JSON encode failed: "..tostring(jsonText))
        return nil
    end
    return jsonText
end

function util.encode(state)
    return ( encode(state) )
end

-- decode
local decode = function(jsonText)
    if not jsonText or jsonText == "" then
        return nil
    end

    local ok, data = pcall(json.decode, jsonText)
    if not ok or type(data) ~= "table" then
        return nil
    end

    return data
end
function util.decode(jsonText)
    return ( decode(jsonText) )
end

-- write
local writeState = function(fileName, state)
    local jsonText = encode(state)
    local writer, _ = getFileWriter(fileName, true, false)
    if not writer then
        print(TAG.."writer not")
        return
    end

    writer:write(jsonText)
    writer:close()
end
-- Helper to dump Java/Lua object keys
function util.inspectObject(obj, filter)
    if not obj then return end
    print("[INSPECT] Inspecting: " .. tostring(obj) .. " (Type: " .. type(obj) .. ")")

    -- Java Object (Userdata with getMethods)
    if obj.getMethods then
        local methods = obj:getMethods()
        for i=0, methods:size()-1 do
            local m = methods:get(i)
            local name = m:getName()
            if not filter or string.find(string.lower(name), string.lower(filter)) then
                print("[INSPECT] Method: " .. name .. "()")
            end
        end
        return
    end

    -- Lua Table
    if type(obj) == "table" then
        for k,v in pairs(obj) do
             if not filter or string.find(string.lower(tostring(k)), string.lower(filter)) then
                print("[INSPECT] Key: " .. tostring(k))
             end
        end
        return
    end
    
    print("[INSPECT] Object is not a table or exposed Java object.")
    print("[INSPECT] Done.")
end

function util.writeState(fileName, state)
    return ( writeState(fileName, state) )
end

-- read
local readState = function(fileName)
    local reader, _ = getFileReader(fileName, true)
    if not reader then
        print(TAG.."reader not")
        return
    end
    
    local tbl = {}
    while true do
        local line = reader:readLine()
        if not line then break end
        table.insert(tbl, line)
    end

    reader:close()

    if #tbl == 0 then
        print("tbl = 0")
        return
    end

    local jsonText = table.concat(tbl)
    return decode(jsonText)
end

function util.readState(fileName)
    return ( readState(fileName) )
end

-- init base game state
local initState = function()
    return {
        timestamp = 0,
        tick = 0,
        player = {
            status = "idle",
            active_action_id = nil,
            position = { x = 0.0, y = 0.0, z = 0 },
            state = {
                aiming = false,
                asleep = false,
                attacking = false,
                bumped = false,
                climbing = false,
                driving = false,
                moving = false,
            },
            rotation = 0,
            body = {},
            moodles = {},
            inventory = {
                held = { primary=nil, secondary=nil },
                worn = {},
                main = {}
            },
            vision = {},
            action_state = {
                status = "idle",
                current_action_id = nil,
                current_action_type = nil,
                sequence_number = -1,
                queue_busy = false
            }
        }
    }
end

function util.initState()
    return ( initState() )
end

-- local initInput = function()
--     return {
--         id = "test_sequence_01",
--         timestamp = 0,
--         clear_queue = false,
--         actions = {
--             { type = "wait", params = { duration_ms = 2000 } },
--             { type = "look_to", params = { x = 10000, y = 10000 } },
--             { type = "wait", params = { duration_ms = 1000 } },
--             { type = "look_to", params = { x = 0, y = 0 } },
--             { type = "sit", params = {} }
--         }
--     }
-- end

local initInput = function()
    return {
        id = "init_idle_state",
        timestamp = 0,
        clear_queue = false,
        actions = {}
    }
end

function util.initInput()
    return ( initInput() )
end

print(TAG.."util.lua loaded!")

return util