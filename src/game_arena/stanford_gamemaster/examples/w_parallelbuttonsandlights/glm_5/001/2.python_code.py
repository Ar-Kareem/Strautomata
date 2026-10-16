
def policy(state: list[list[object]], role: str) -> str:
    """
    Policy for parallelbuttonsandlights game.
    
    Strategy:
    - If we just played (played, role exists), return 'tick'
    - Otherwise, select button based on step number (cycling a, b, c)
    """
    # Check if we just played - if so, tick to advance
    for prop in state:
        if len(prop) >= 2 and prop[0] == "played" and prop[1] == role:
            return "tick"
    
    # Get the step number from state
    step = 1
    for prop in state:
        if len(prop) >= 2 and prop[0] == "step":
            try:
                step = int(prop[1])
            except (ValueError, TypeError):
                step = 1
            break
    
    # Choose button based on step (cycling a, b, c)
    # Pattern: step % 3 == 1 -> a, == 2 -> b, == 0 -> c
    if step % 3 == 1:
        return f"a({role})"
    elif step % 3 == 2:
        return f"b({role})"
    else:
        return f"c({role})"
