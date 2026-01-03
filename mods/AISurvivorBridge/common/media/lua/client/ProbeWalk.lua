local function probeWalkTo()
    if ISWalkToAction then
        print("[Probe] ISWalkToAction FOUND!")
    else
        print("[Probe] ISWalkToAction NOT found.")
    end
    
    if ISTimedActionQueue then
        print("[Probe] ISTimedActionQueue FOUND!")
    end
end

Events.OnGameStart.Add(probeWalkTo)
