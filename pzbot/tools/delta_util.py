def compute_delta(old: dict, new: dict) -> dict:
    """
    Computes a recursive difference between two dictionaries.
    Returns None if identical.
    Returns a dict containing only Changed or New fields.
    Deleted fields are represented by explicit None (if we want to track deletions? 
    For recording, we keyframe often enough that explicit deletions might be overkill, 
    but let's try to be precise).
    
    Strategy:
    - If type mismatch -> return new
    - If dict -> recurse keys
    - If list -> compare full list (diffing lists by index is messy for game state arrays) -> return new
    - If leaf value equal -> return Nothing (omit from delta)
    - If leaf value diff -> return new
    """
    if old is None: return new
    if type(old) != type(new): return new
    
    # Primitives and Lists (treat lists as atomic for now for speed/simplicity)
    if not isinstance(new, dict):
        if old == new: return None
        return new
    
    delta = {}
    
    # Check all keys in NEW
    for k, v_new in new.items():
        v_old = old.get(k)
        
        # Recurse
        diff = compute_delta(v_old, v_new)
        
        # If there is a difference, keep it
        if diff is not None:
            delta[k] = diff
            
    # Check for DELETED keys (keys in OLD but not in NEW)
    # We represent deletion as setting to None? Or just ignore for now?
    # In Game State, fields rarely disappear, they usually become empty lists/dicts.
    # But if they do, we need to know.
    # Let's use a special sentinel for deletion? Or just rely on Keyframes.
    # For a Recording, Keyframes every few seconds heal synchronization drift.
    # So we can ignore explicit deletions for simplicity, assuming the next Keyframe fixes it.
    # This keeps the delta extremely small.
    
    if not delta: return None
    return delta

def apply_delta(base: dict, delta: dict) -> dict:
    """
    Applies a delta to a base dictionary (Transformation).
    This logic needs to match compute_delta exactly.
    """
    import copy
    if base is None: return delta
    if delta is None: return base
    
    # If delta is replacing the whole object (type mismatch or primitive)
    if not isinstance(delta, dict) or not isinstance(base, dict):
        return delta
        
    # We mutate a copy
    result = copy.deepcopy(base)
    
    for k, v in delta.items():
        result[k] = apply_delta(result.get(k), v)
        
    return result
