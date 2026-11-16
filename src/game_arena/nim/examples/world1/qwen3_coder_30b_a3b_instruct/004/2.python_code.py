
def policy(piles: list[int]) -> str:
    # Convert to a more convenient form
    state = piles[:]
    
    # Calculate nim-sum
    nim_sum = 0
    for pile in state:
        nim_sum ^= pile
    
    # Find a winning move
    # If nim-sum is 0, we're in losing position, but have to make a move
    # If nim-sum is not 0, we can make a move to set nim-sum to 0
    
    if nim_sum == 0:
        # We're in a losing position. Make any legal move
        # Prefer removing from larger piles to keep game going longer
        for i in range(len(state)):
            if state[i] > 1:
                return f"{i},{1}"
        # If we're at [1,1,1,1] or similar, we're forced to lose, 
        # but make a move that maintains some resistance
        for i in range(len(state)):
            if state[i] > 0:
                return f"{i},{1}"
    else:
        # We're in a winning position. Find a move that makes nim-sum 0
        for i in range(len(state)):
            if state[i] > 0:
                # Try to make a move such that (state[i] - take) XOR new_nim_sum = 0
                # This means: new_nim_sum = nim_sum XOR state[i]
                target = nim_sum ^ state[i]
                if target < state[i]:
                    return f"{i},{state[i] - target}"
    
    # Fallback, should never reach here in valid game state
    for i in range(len(state)):
        if state[i] > 0:
            return f"{i},1"
