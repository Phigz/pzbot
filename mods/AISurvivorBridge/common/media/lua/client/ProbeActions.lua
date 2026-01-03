local function probeGlobals()
    print("[Probe] Dumping IS* Globals...")
    local count = 0
    for k,v in pairs(_G) do
        if type(k) == "string" and k:sub(1,2) == "IS" then
            if k:find("Walk") or k:find("Move") or k:find("Path") or k:find("Action") then
                print("[Probe] Found: " .. k .. " (" .. type(v) .. ")")
                count = count + 1
            end
        end
    end
    print("[Probe] Found " .. count .. " candidates.")
    
    -- Specific check for TimedActions path
    print("[Probe] require 'TimedActions/ISWalkToAction' test...")
    local ok, res = pcall(require, "TimedActions/ISWalkToAction")
    print("[Probe] Result: " .. tostring(ok) .. " | " .. tostring(res))
end

Events.OnGameStart.Add(probeGlobals)
