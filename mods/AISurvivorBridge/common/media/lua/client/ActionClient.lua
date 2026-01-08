-- ActionClient.lua
-- Reads input commands from disk and dispatches them to the ActionExecutor.

local function safeRequire(name)
    local ok, mod = pcall(require, name)
    if not ok then
        print("[AISurvivorBridge-Action] CRITICAL ERROR: Failed to require " .. name .. ": " .. tostring(mod))
        return nil
    end
    return mod
end

local util = safeRequire("util")
local ActionExecutor = safeRequire("ActionExecutor")
local Navigator = safeRequire("Navigation/Navigator")

local function log_info(msg) if Logger then Logger.info("ActionClient", msg) else print("[ActionClient] "..tostring(msg)) end end
local function log_debug(msg) if Logger then Logger.debug("ActionClient", msg) else print("[ActionClient-DEBUG] "..tostring(msg)) end end
local function log_error(msg) if Logger then Logger.error("ActionClient", msg) else print("[ActionClient] ERROR: "..tostring(msg)) end end

log_info("Loading...")
local INPUT_FILE_NAME = "AISurvivorBridge/input.json"

local ActionClient = {}
_G.AISurvivorBridge_ActionClient = ActionClient

local lastSequenceNumber = -1
local completedActionIDs = {} -- Set of executed action IDs
local currentAction = nil
local currentBatchActions = {} -- Maintain the current list of actions
local lastCompletedActionId = nil
local lastCompletedResult = "success"

function ActionClient.OnGameStart()
    log_info("Ready.")
end

local lastCheckTime = 0
local function getTimeMs()
    if getTimeInMillis then return getTimeInMillis() end
    return 0 -- Fallback or error?
end

function ActionClient.OnPlayerUpdate(player)
    if not player or player ~= getPlayer() then return end

    -- NAVIGATOR UPDATE TICK
    if Navigator then 
        -- print("[ActionClient] Ticking Navigator...")
        Navigator.update(player) 
    else
        print("[ActionClient] Navigator is NIL!")
    end

    local now = getTimeMs()
    if now - lastCheckTime > 500 then
        lastCheckTime = now
    else
        return 
    end

    local input = util.readState(INPUT_FILE_NAME)
    if not input then 
        log_debug("readState returned nil for " .. INPUT_FILE_NAME)
        return 
    end

    -- Process Batch
    local inputSeq = input.sequence_number or -1
    
    -- New Batch or Updated Batch
    if inputSeq > lastSequenceNumber then
        log_info("New Sequence Detected: " .. tostring(inputSeq) .. " > Old: " .. tostring(lastSequenceNumber))
        lastSequenceNumber = inputSeq
        
        -- Clear queue if requested
        if input.clear_queue then
            log_info("Clearing Queue (requested)")
            ISTimedActionQueue.clear(player)
            currentAction = nil
            completedActionIDs = {} -- Reset memory on clear
        end

        currentBatchActions = input.actions or {}
        log_info("Loaded " .. #currentBatchActions .. " actions.")
    elseif inputSeq < lastSequenceNumber then
    end

    -- Execution Logic
    ActionClient.updateExecution(player)
end

function ActionClient.updateExecution(player)
    local queue = ISTimedActionQueue.getTimedActionQueue(player)
    local isbusy = false
    if queue and queue.queue then
        if queue.queue.isEmpty then
             isbusy = not queue.queue:isEmpty()
        else
             isbusy = (#queue.queue > 0)
        end
    end

    -- Check Navigator
    if Navigator and Navigator.isMoving then
        isbusy = true
    end

    -- Check if current action finished
    if not isbusy and currentAction then
        log_info("Action Finished: " .. (currentAction.type or "unknown"))
        if currentAction.id then
            completedActionIDs[currentAction.id] = true
            lastCompletedActionId = currentAction.id
            lastCompletedResult = "success"
        end
        currentAction = nil
    end

    -- If idle, pick next action
    if not isbusy and not currentAction then
        -- log_debug("Idle and no current action, checking batch...") 
        for i, action in ipairs(currentBatchActions) do
            local id = action.id
            if id then
                if not completedActionIDs[id] then
                    -- Found a new action to run
                    log_info("Starting Action " .. i .. ": " .. (action.type or "unknown") .. " [ID: " .. tostring(id) .. "]")
                    
                    local ok = ActionExecutor.execute(action, player)
                    if ok then
                        log_info("Action Started Successfully.")
                        currentAction = action
                        return -- Start one at a time for now
                    else
                        log_error("Failed to start action " .. i)
                        completedActionIDs[id] = true 
                        lastCompletedActionId = id
                        lastCompletedResult = "failed_start"
                    end
                else
                end
            else
                 log_error("Action missing ID at index " .. i)
            end
        end
    end
end

function ActionClient.getStatus(player)
    if not player then return nil end
    
    local isbusy = false
    local queue = ISTimedActionQueue.getTimedActionQueue(player)
    if queue and queue.queue then
        if queue.queue.isEmpty then
             isbusy = not queue.queue:isEmpty()
        else
             isbusy = (#queue.queue > 0)
        end
    end

    -- Check Navigator
    if Navigator and Navigator.isMoving then
        isbusy = true
    end

    local status = "idle"
    if currentAction or isbusy then
        status = "executing"
    end

    local completed_ids_list = {}
    for id, _ in pairs(completedActionIDs) do
        table.insert(completed_ids_list, id)
    end

    return {
        status = status, -- executing / idle
        sequence_number = lastSequenceNumber,
        current_action_id = currentAction and currentAction.id,
        current_action_type = currentAction and currentAction.type,
        queue_busy = isbusy,
        last_completed_action_id = lastCompletedActionId,
        last_completed_result = lastCompletedResult,
        completed_ids = completed_ids_list
    }
end

Events.OnGameStart.Add(ActionClient.OnGameStart)
Events.OnPlayerUpdate.Add(ActionClient.OnPlayerUpdate)

log_info("Loaded!")
return ActionClient
