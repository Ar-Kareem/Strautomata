
def policy(you: list[int], opponent: list[int]) -> int:
    # Prioritize capturing seeds if possible
    for i in range(6):
        if you[i] > 0:  # Only consider non-empty houses
            last_seed_position = (i + you[i]) % 14
            
            # Check if we land in our store
            if last_seed_position == 6:
                return i  # Prefer this move for the extra turn
            
            # Check for potential capture
            if last_seed_position < 6 and you[last_seed_position] == 0:
                opponent_house = opponent[5 - last_seed_position]
                if opponent_house > 0:
                    return i  # This move allows for a capture
    
    # If no captures are available, just return the first non-empty house
    for i in range(6):
        if you[i] > 0:
            return i
    
    # Fallback (should never reach here, as policy is only called with valid moves)
    raise Exception("No valid moves available, called policy in an invalid game state.")
