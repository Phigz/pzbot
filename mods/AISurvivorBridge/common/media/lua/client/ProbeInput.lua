local function probeInput()
    print("[Probe] Starting Input API Probe...")
    
    local classes = {
        "zombie.input.GameKeyboard",
        "zombie.input.KeyboardState",
        "zombie.core.Core",
        "zombie.input.Input"
    }

    for _, clsName in ipairs(classes) do
        local cls = loadstring("return " .. clsName)()
        if cls then
            print("[Probe] Class found: " .. clsName)
            -- Dump methods
            for k,v in pairs(cls) do
                 print("[Probe] " .. clsName .. "." .. tostring(k) .. " (" .. type(v) .. ")")
            end
        else
            print("[Probe] Class NOT found/loadable: " .. clsName)
        end
    end
    
    print("[Probe] Input Probe Complete.")
end

Events.OnGameStart.Add(probeInput)
