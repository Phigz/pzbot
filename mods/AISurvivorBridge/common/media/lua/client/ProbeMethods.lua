local util = require("util")

local function probeMethods()
    local player = getSpecificPlayer(0)
    if not player then return end

    print("[ProbeMethods] Starting deep scan of IsoPlayer...")

    -- Helper to print methods
    local function dumpMethods(obj, filter)
        if not obj then return end
        local classObj = obj.getClass and obj:getClass()
        if not classObj then 
            print("[ProbeMethods] No getClass() found on " .. tostring(obj))
            return 
        end
        
        local methods = classObj:getMethods()
        for i=0, methods.length-1 do
            local m = methods[i]
            local name = m:getName()
            if not filter or string.find(string.lower(name), string.lower(filter)) then
                print("[ProbeMethods] Found Method: " .. name)
            end
        end
    end

    print("[ProbeMethods] Starting deep scan of IsoPlayer...")
    
    local keywords = {"setLx", "setLy", "Move", "Input", "Target", "Path", "Controller", "Vector", "Angle", "Dir"}
    
    for _, k in ipairs(keywords) do
        dumpMethods(player, k)
    end
    
    -- Also check the "InputState" if it exists
    if player.getInputState then
        print("[ProbeMethods] Found getInputState(), inspecting...")
        util.inspectObject(player:getInputState())
    end
end

Events.OnGameStart.Add(probeMethods)
