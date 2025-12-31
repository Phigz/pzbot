-- Dispatches commands to modular handlers in Actions/ directory.

local ActionExecutor = {}
local TAG = "[AISurvivorBridge] "
print(TAG.."ActionExecutor.lua loading..")

-- Registry of handlers
local handlers = {}

local function getHandler(actionType)
    if handlers[actionType] then return handlers[actionType] end
    
    local moduleName = "Actions/Handler_" .. actionType:gsub("^%l", string.upper)
    print(TAG .. "Attempting to require: " .. moduleName)
    local ok, handler = pcall(require, moduleName)
    
    if ok and handler then
        handlers[actionType] = handler
        return handler
    else
        print(TAG .. "Require failed for " .. moduleName .. ": " .. tostring(handler))
        -- Try exact match
        local ok2, handler2 = pcall(require, "Actions/Handler_" .. actionType)
        if ok2 and handler2 then
            handlers[actionType] = handler2
            return handler2
        else
            print(TAG .. "Require failed for exact match: " .. tostring(handler2))
        end
    end
    
    print(TAG .. "No handler found for action type: " .. actionType)
    return nil
end

-- Explicit mappings for common/legacy names
handlers["move_to"] = require("Actions/Handler_MoveTo")
handlers["moveto"]  = require("Actions/Handler_MoveTo") -- Alias
handlers["walk"]    = require("Actions/Handler_MoveTo") -- Legacy Alias

handlers["look_to"] = require("Actions/Handler_LookTo")
handlers["lookto"]  = require("Actions/Handler_LookTo") -- Alias
handlers["look"]    = require("Actions/Handler_LookTo") -- Legacy Alias

handlers["toggle_crouch"] = require("Actions/Handler_ToggleCrouch")
handlers["togglecrouch"]  = require("Actions/Handler_ToggleCrouch") -- Alias

handlers["wait"]    = require("Actions/Handler_Wait")
handlers["sit"]     = require("Actions/Handler_Sit")
handlers["debug_spawn"] = require("Actions/Handler_DebugSpawn")

-- Returns true if accepted, false if rejected/error.
function ActionExecutor.execute(action, player)
    if not action or not action.type then return false end

    print(TAG .. "[BotCommand] Dispatching action: " .. action.type)

    local handler = getHandler(action.type)
    if handler then
        return handler.execute(player, action.params or action)
    end

    print(TAG .. "Unknown or missing handler for: " .. action.type)
    return false
end

-- Probe for Sit Actions
print("[AISurvivorBridge] PROBE STARTING: Searching for 'Sit'...")
for k, v in pairs(_G) do
    if type(k) == "string" and string.find(k, "Sit") then
        print("[AISurvivorBridge] PROBE FOUND: " .. k)
    end
end
print("[AISurvivorBridge] PROBE COMPLETE.")

print(TAG.."ActionExecutor.lua loaded!")
return ActionExecutor
