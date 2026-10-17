
def policy(piles: list[int]) -> str:
    """
    Determines the optimal move for Misère Nim (4 piles).
    The player taking the last object loses.
    """
    
    # Calculate Nim-sum (XOR sum)
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
        
    # Identify if all piles are effectively size 0 or 1
    only_ones = all(p <= 1 for p in piles)
    
    # Helper to simulate a move and check if it leaves [1, 0, 0, 0]
    def is_bad_terminal_move(pile_idx, take_count):
        new_piles = list(piles)
        new_piles[pile_idx] -= take_count
        # Count piles with exactly 1 stone
        ones = sum(1 for x in new_piles if x == 1)
        zeros = sum(1 for x in new_piles if x == 0)
        return ones == 1 and zeros == 3

    # CASE 1: All piles are 0 or 1
    if only_ones:
        # Count ones
        count_ones = sum(piles)
        
        # If odd number of 1s, we are in a losing position (assuming optimal opponent).
        # If even number of 1s, we are in a winning position.
        
        if count_ones % 2 == 0:
            # Winning: Take 1 from any pile to leave odd number of 1s
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
        else:
            # Losing: We are forced to leave an even number of 1s.
            # We choose any valid move (usually 1 stone).
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"

    # CASE 2: At least one pile has > 1 stone
    else:
        if nim_sum == 0:
            # Current player is in a losing position. 
            # We must make a move. We try to minimize damage.
            # Generally, we take 1 from the first available pile.
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
        else:
            # Current player is in a winning position.
            # Find a move that makes nim_sum = 0.
            for i in range(4):
                target = piles[i] ^ nim_sum
                if target < piles[i]:
                    take = piles[i] - target
                    # Check for the [1, 0, 0, 0] trap
                    if not is_bad_terminal_move(i, take):
                        return f"{i},{take}"
            
            # If the standard winning move creates [1, 0, 0, 0], 
            # we look for any alternative move that resets Nim-sum to 0.
            for i in range(4):
                target = piles[i] ^ nim_sum
                if target < piles[i]:
                    take = piles[i] - target
                    return f"{i},{take}"
                    
            # Fallback (should not be reached if nim_sum != 0 and piles valid)
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"

    # Fallback return (should not be reached)
    return "0,1"
