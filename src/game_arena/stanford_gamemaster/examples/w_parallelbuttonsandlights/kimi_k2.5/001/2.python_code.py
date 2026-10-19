
def policy(state: list[list[object]], role: str) -> str:
    # Check if we have already played our main action this step
    for fact in state:
        if fact[0] == "played" and fact[1] == role:
            return "tick"
    
    # Find the current step number
    step_num = None
    for fact in state:
        if fact[0] == "step":
            step_num = int(fact[1])
            break
    
    # Default fallback (should not occur in valid states)
    if step_num is None:
        return "tick"
    
    # Determine which button to press based on step number modulo 3
    remainder = step_num % 3
    if remainder == 1:
        return f"a({role})"
    elif remainder == 2:
        return f"b({role})"
    else:  # remainder == 0
        return f"c({role})"
