
def policy(piles: list[int]) -> str:
    """
    Calculates the optimal move for a game of Misère Nim (4 piles).
    The player taking the last object loses.
    """
    # Identify non-zero piles to check for the "all ones" scenario
    non_zero_piles = [p for p in piles if p > 0]
    
    # Case 1: All non-zero piles are of size 1
    # In this case, the winning condition depends on the parity of the count of 1-piles.
    if all(p == 1 for p in non_zero_piles):
        # If count is even: take 1 (winning move).
        # If count is odd: take 1 (forced losing move, or heuristic).
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
    
    # Case 2: At least one pile has size > 1
    # Calculate the Nim-sum (XOR of all piles)
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
        
    if nim_sum != 0:
        # Winning Position: Find a move to make nim_sum 0
        for i, p in enumerate(piles):
            target = p ^ nim_sum
            if target < p:
                # This move makes the nim_sum zero.
                take = p - target
                
                # Check for Misère Nim edge case:
                # Does this move result in a state with ALL piles size 1 and an EVEN count?
                # (Such a state is a Win for the next player in Misère, so we must avoid it).
                
                # Count 1s in the other piles
                ones_in_others = 0
                for j, val in enumerate(piles):
                    if i != j and val == 1:
                        ones_in_others += 1
                
                resulting_ones = -1
                if target == 1:
                    # We are creating a new pile of 1
                    resulting_ones = ones_in_others + 1
                elif target == 0:
                    # We are removing a pile. 
                    # If all others are 1, resulting count is ones_in_others.
                    resulting_ones = ones_in_others
                
                # If the resulting state is all 1s and the count is even (including 0), it's a bad move.
                if resulting_ones != -1 and resulting_ones % 2 == 0:
                    if target == 1:
                        # Instead of reducing to 1 (making count even), remove the entire pile.
                        # This leaves count = ones_in_others (which is Odd).
                        return f"{i},{p}"
                    elif target == 0:
                        # Instead of removing pile (making count even), reduce to 1.
                        # This leaves count = ones_in_others + 1 (which is Odd).
                        return f"{i},{p - 1}"
                
                # Standard safe move
                return f"{i},{take}"
    
    # Case 3: Losing Position (nim_sum == 0)
    # No winning move exists. Use a heuristic: take 1 from the largest pile.
    # This is a standard defensive strategy to prolong the game or force errors.
    max_val = -1
    max_idx = -1
    for i, p in enumerate(piles):
        if p > max_val:
            max_val = p
            max_idx = i
            
    # Fallback: If logic fails (e.g., invalid state passed), take 1 from first available
    if max_idx == -1:
        for i, p in enumerate(piles):
            if p > 0: return f"{i},1"
        
    return f"{max_idx},1"
