
def policy(piles: list[int]) -> str:
    """
    Returns the next move for a Misere Nim game (4 piles).
    Format: 'pile,take' where pile is 0-3 and take is amount to remove.
    """
    # Identify indices of piles with more than 1 item
    large_pile_indices = [i for i, p in enumerate(piles) if p > 1]
    
    move_pile = -1
    move_take = -1

    # STRATEGY: MISERE EXCEPTION
    # If exactly one pile is > 1, we must leave an ODD number of piles of size 1.
    if len(large_pile_indices) == 1:
        idx = large_pile_indices[0]
        # Count current piles of size 1 (excluding the large one, obviously)
        ones_count = sum(1 for p in piles if p == 1)
        
        # If ones_count is even, we need to add a 1 (reduce large pile to 1).
        # Total ones becomes (even + 1) = odd.
        # If ones_count is odd, we need to add 0 (reduce large pile to 0).
        # Total ones becomes (odd + 0) = odd.
        if ones_count % 2 == 0:
            target_size = 1
        else:
            target_size = 0
            
        move_pile = idx
        move_take = piles[idx] - target_size

    # STRATEGY: NORMAL NIM
    # If there are 0 or >= 2 large piles, standard Nim-sum logic applies.
    # (Note: if 0 large piles, only 1s remain, implies Nim-sum logic works or moves are forced).
    else:
        nim_sum = 0
        for p in piles:
            nim_sum ^= p
        
        if nim_sum != 0:
            # Winning position: find a move to make nim_sum 0
            for i, p in enumerate(piles):
                target = p ^ nim_sum
                if target < p:
                    move_pile = i
                    move_take = p - target
                    break
        else:
            # Losing position: must make a move. Take 1 from first non-empty pile.
            for i, p in enumerate(piles):
                if p > 0:
                    move_pile = i
                    move_take = 1
                    break
    
    return f"{move_pile},{move_take}"
