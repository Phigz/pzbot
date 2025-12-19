local function safeRequire(name)
    local ok, mod = pcall(require, name)
    if not ok then
        print("[AutoLoader] Failed to require " .. name)
        return nil
    end
    return mod
end
local Logger = safeRequire("Logger")
local function log(msg) 
    if Logger then Logger.info("AutoLoader", msg) else print("[AutoLoader] " .. tostring(msg)) end 
end

log("Initializing...")

local tickCount = 0
local loaded = false

-- Configuration
local CONFIG = {
    ENABLED = true,
    MAX_WAIT_TICKS = 600, -- 10 seconds
    POST_LOAD_DELAY = 300, -- 5 seconds after player detection
    FORCE_NEW_GAME = false, -- For verification
}



local function attemptLoad()
    if not MainScreen or not MainScreen.instance then return end
    
    local ms = MainScreen.instance
    
    -- Read Launch Config
    local launchMode = "continue"
    local reader = getFileReader("AISurvivorBridge/launch_config.json", true)
    if reader then
        local line = reader:readLine()
        while line do
            if string.find(line, "new_game") then 
                launchMode = "new_game"
            elseif string.find(line, "done") then 
                launchMode = "done" 
            end
            line = reader:readLine()
        end
        reader:close()
    else
        log("Could not open launch_config.json")
    end
    log("Launch Config Mode: " .. launchMode)
    
    -- CHECK FLAG: Config Consumed
    if launchMode == "done" then
        log("AutoLoad already performed (derived from launch_config). Stopping listener.")
        loaded = true
        Events.OnPreUIDraw.Remove(loadLoop)
        return
    end

    -- CONSUME CONFIG (Mark as done)
    -- We overwrite the config to ensure next time we see "done"
    local writer = getFileWriter("AISurvivorBridge/launch_config.json", true, false)
    if writer then
        writer:write("{\"mode\": \"done\"}")
        writer:close()
    else
        log("Error: Could not update launch_config.json directly.")
    end
    
    -- Check if we can continue a save
    if launchMode ~= "new_game" and ms.continueLatestSave and ms.latestSaveWorld then
        local mode = ms.latestSaveGameMode
        local world = ms.latestSaveWorld
        
        log("Found Save: " .. tostring(world) .. " (" .. tostring(mode) .. ")")
        log("Loading...")
        
        loaded = true
        Events.OnPreUIDraw.Remove(loadLoop)
        
        -- Trigger load
        ms.continueLatestSave(mode, world)
    else
        log("No save found or New Game requested. Starting New Sandbox Game...")
        
        -- Default Sandbox Setup
        if MainScreen.instance.sandboxOptions then
             MainScreen.instance.sandboxOptions:resetToDefault()
             MainScreen.instance.sandboxOptions:updateFromLua()
        end

        local worldName = "pz-bot-" .. tostring(ZombRand(1000000))
        
        getWorld():setWorld(worldName)
        getWorld():setGameMode("Sandbox")
        getWorld():setMap("Muldraugh, KY;Riverside, KY;Rosewood, KY;West Point, KY;Echo Creek, KY")
        
        if createWorld then
             log("Calling GLOBAL createWorld(" .. worldName .. ")...")
             createWorld(worldName)
             
             if MainScreen.instance.desc then
                 MainScreen.instance.desc:setForename("Bot")
                 MainScreen.instance.desc:setSurname("User")
             end
             
             if LoadingQueueState and forceChangeState then
                 log("Transitioning to LoadingQueueState...")
                 forceChangeState(LoadingQueueState.new())
             elseif GameLoadingState and forceChangeState then
                 log("LoadingQueueState not found, trying GameLoadingState...")
                 forceChangeState(GameLoadingState.new())
             else
                 log("ERROR: Could not find state classes or forceChangeState!")
             end
        else
             log("ERROR: createWorld global function not found!")
        end
        
        loaded = true
        Events.OnPreUIDraw.Remove(loadLoop)
    end
    log("Load initiated. External script should handle 'Click to Start'.")
end

local function loadLoop()
    if loaded then return end
    tickCount = tickCount + 1
    
    if tickCount > CONFIG.MAX_WAIT_TICKS then
        log("Timed out waiting for MainScreen.")
        Events.OnPreUIDraw.Remove(loadLoop)
        return
    end
    
    attemptLoad()
end

if CONFIG.ENABLED then
    Events.OnPreUIDraw.Add(loadLoop)
end
