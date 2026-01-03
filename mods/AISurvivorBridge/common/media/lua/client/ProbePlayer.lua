local function probePlayer()
    local player = getPlayer()
    if not player then return end
    
    print("[Probe] Probing IsoPlayer for Input methods...")
    
    -- Get metatable or traversing the userdata if possible
    -- LuaJava often exposes methods via pairs check or just list them if we know how 
    -- But since we can't iterate userdata keys easily without a helper, we'll try to guess/check typical names.
    
    local candidates = {
        "setLeft", "setRight", "setUp", "setDown",
        "setForward", "setBackward",
        "setMoveLeft", "setMoveRight", "setMoveUp", "setMoveDown",
        "setIsMoveLeft", "setIsMoveRight", 
        "setForceLeft", "setForceRight",
        "PressLeft", "PressRight",
        "setInput"
    }
    
    for _, name in ipairs(candidates) do
        if player[name] then
            print("[Probe] FOUND METHOD: player:" .. name .. " - " .. type(player[name]))
        end
    end
    
    -- Also list all keys containing "Left", "Right", "Up", "Down" if we can iterate
    -- (This depends on how PZ exposes userdata to pairs, usually it doesn't work on userdata, but let's try getmetatable)
    local mt = getmetatable(player)
    if mt then
        print("[Probe] Metatable found.")
        for k,v in pairs(mt) do
             if type(k) == "string" and (k:find("Left") or k:find("Right") or k:find("Up") or k:find("Down") or k:find("Input")) then
                 print("[Probe] MT Key: " .. k .. " (" .. type(v) .. ")")
             end
             -- Also check __index tables if accessible
             if k == "__index" and type(v) == "table" then
                  for ik, iv in pairs(v) do
                      if type(ik) == "string" and (ik:find("Left") or ik:find("Right") or ik:find("Up") or ik:find("Down") or ik:find("Input")) then
                         print("[Probe] Index Key: " .. ik .. " (" .. type(iv) .. ")")
                      end
                  end
             end
        end
    end

    print("[Probe] Player Probe Complete.")
end

Events.OnGameStart.Add(probePlayer)
