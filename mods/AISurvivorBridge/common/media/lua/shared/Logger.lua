Logger = {}
_G.AISurvivorBridge_Logger = Logger

-- Default Log Level
local currentLevel = 2 -- INFO
local LEVELS = {
    DEBUG = 1,
    INFO = 2,
    WARN = 3,
    ERROR = 4
}
local LEVEL_NAMES = {
    [1] = "DEBUG",
    [2] = "INFO",
    [3] = "WARN",
    [4] = "ERROR"
}

function Logger.loadConfig()
    local reader = getFileReader("AISurvivorBridge/launch_config.json", true)
    if reader then
        local line = reader:readLine()
        while line do
            -- Simple string match for log_level ignoring whitespace
            for k, v in pairs(LEVELS) do
                if string.find(string.upper(line), '"LOG_LEVEL"%s*:%s*"' .. k .. '"') then
                    currentLevel = v
                    print("[Logger] Level set to " .. k)
                end
            end
            line = reader:readLine()
        end
        reader:close()
    else
        print("[Logger] launch_config.json not found, using default INFO")
    end
end

local function log(level, tag, msg)
    if level >= currentLevel then
        local prefix = string.format("[%s] [%s] ", LEVEL_NAMES[level], tag)
        print(prefix .. tostring(msg))
    end
end

function Logger.debug(tag, msg)
    log(LEVELS.DEBUG, tag, msg)
end

function Logger.info(tag, msg)
    log(LEVELS.INFO, tag, msg)
end

function Logger.warn(tag, msg)
    log(LEVELS.WARN, tag, msg)
end

function Logger.error(tag, msg)
    log(LEVELS.ERROR, tag, msg)
end

-- Attempt to load config immediately
Logger.loadConfig()

return Logger
