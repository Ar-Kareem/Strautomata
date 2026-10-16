
def policy(state: list[list[object]], role: str) -> str:
    # Convert state to a more accessible format (set of tuples)
    facts = {tuple(f) for f in state}
    
    # Check if we have already acted this turn
    if (("played", role),) in [(tuple(x),) for x in state]:
        return "tick"
    
    # Identify the current step
    step = 0
    for fact in state:
        if fact[0] == "step":
            step = int(fact[1])
            break
            
    # If we haven't played, choose an action based on role and step
    # Based on the provided examples:
    # Left: Turn 0 -> a(left), Turn 12 -> a(left), Turn 20 -> b(left)
    # Right: Turn 2 -> b(right), Turn 10 -> c(right)
    
    if role == "left":
        if step % 8 < 4:
            return "a(left)"
        else:
            return "b(left)"
    else: # role == "right"
        if step % 8 < 4:
            return "b(right)"
        else:
            return "c(right)"
