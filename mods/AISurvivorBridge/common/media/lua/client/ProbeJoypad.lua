local function probeSystem()
    print("[ProbeJoypad] Checking JoypadManager...")
    if JoypadManager then
        print("[ProbeJoypad] JoypadManager FOUND.")
        -- Check for save/load methods
        for k,v in pairs(JoypadManager) do
            print("[ProbeJoypad] JoypadManager field: " .. tostring(k))
        end
    else
        print("[ProbeJoypad] JoypadManager NOT found.")
    end

    local player = getSpecificPlayer(0)
    if player then
        print("[ProbeJoypad] Checking IsoPlayer for Joypad methods...")
        local methods = player:getClass():getMethods()
        for i=0, methods.length-1 do
            local m = methods[i]
            local name = m:getName()
            -- Filter for Joypad or Input
            if string.find(string.lower(name), "joypad") or 
               string.find(string.lower(name), "input") or
               string.find(string.lower(name), "setisattemptingtowa") then -- setIsAttemptingToWalk?
                print("[ProbeJoypad] Found Method: " .. name)
            end
        end
    end
end

Events.OnGameStart.Add(probeSystem)
