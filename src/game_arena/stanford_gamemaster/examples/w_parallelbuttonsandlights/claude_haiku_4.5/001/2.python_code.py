
def policy(state: list[list[object]], role: str) -> str:
    """
    Policy for parallelbuttonsandlights game.
    
    Strategy:
    1. If we've already played this turn (["played", role] exists), play "tick"
    2. Otherwise, play a button action (a, b, or c) in a cycling pattern
    """
    
    # Check if we've already played this turn
    has_played = any(fact[0] == "played" and len(fact) > 1 and fact[1] == role 
                     for fact in state)
    
    if has_played:
        # We've played our button, now we must tick to end our turn
        return "tick"
    else:
        # We need to play a button action
        # Use step number to cycle through buttons a, b, c
        step = 1
        for fact in state:
            if fact[0] == "step" and len(fact) > 1:
                try:
                    step = int(fact[1])
                except (ValueError, IndexError):
                    pass
                break
        
        # Cycle through buttons: a, b, c, a, b, c, ...
        button_options = ["a", "b", "c"]
        button_index = (step - 1) % 3
        button = button_options[button_index]
        
        return f"{button}({role})"
