local util = require("util")

local function probeInputMethods()
    local player = getSpecificPlayer(0)
    print("[ProbeInput] Checking GameKeyboard...")
    
    -- Check if GameKeyboard is available global
    if GameKeyboard then
        print("[ProbeInput] GameKeyboard found.")
        util.inspectObject(GameKeyboard, "Key")
    else
        -- Try loading it?
        -- It's usually exposed as a static class if Kahlua allows.
        print("[ProbeInput] GameKeyboard global not found.")
    end
    
    print("[ProbeInput] Checking Player methods for 'Forward'...")
    -- We want to see if there's a boolean toggle for movement
    local candidates = {"setMoveForward", "setIsAttemptingToMove", "setForceRun", "setAuthorizeMove", "setIgnoreInputs"}
    
    if player and player.getClass then
        local methods = player:getClass():getMethods()
        for i=0, methods.length-1 do
            local m = methods[i]
            local name = m:getName()
            for _, c in ipairs(candidates) do
                if string.find(string.lower(name), string.lower(c)) then
                    print("[ProbeInput] Found Method: " .. name)
                end
            end
        end
    end
end

Events.OnGameStart.Add(probeInputMethods)
