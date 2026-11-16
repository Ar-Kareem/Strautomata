
def policy(piles: list[int]) -> str:
    """
    Returns the next move for Misère Nim (4 piles).
    Format: 'pile_index,amount_to_remove'
    """
    # Phase 1: All piles are 0 or 1 (endgame)
    # In Misère Nim with all 1s, leave an ODD number of piles.
    if all(p <= 1 for p in piles):
        count_ones = sum(piles)
        # Find any pile with a 1 and take it
        for i, p in enumerate(piles):
            if p == 1:
                return f"{i},1"
        # Should not reach here if game is ongoing (would be terminal)
        return "0,0"
    
    # Phase 2: At least one pile > 1 - use Nim-sum strategy
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # Losing position - make any legal move
    if nim_sum == 0:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
    
    # Winning position - find a move to make nim_sum 0
    for i, p in enumerate(piles):
        new_val = p ^ nim_sum
        if new_val < p:
            # Check if this move results in all piles being 0 or 1
            others_all_one = all(piles[j] <= 1 for j in range(len(piles)) if j != i)
            
            if others_all_one and new_val <= 1:
                # Misère adjustment: ensure we leave an ODD number of 1s
                ones_in_others = sum(1 for j in range(len(piles)) if j != i and piles[j] == 1)
                total_ones = ones_in_others + (1 if new_val == 1 else 0)
                
                if total_ones % 2 == 0:
                    # Would leave even (losing), so flip the parity
                    if new_val == 0:
                        # Instead of taking all, leave 1 (take p-1)
                        return f"{i},{p - 1}"
                    else:  # new_val == 1
                        # Instead of leaving 1, take all (leave 0)
                        return f"{i},{p}"
                else:
                    # Already leaves odd, proceed with normal Nim move
                    return f"{i},{p - new_val}"
            else:
                # Normal Nim move (not entering pure 1s endgame)
                return f"{i},{p - new_val}"
    
    # Fallback (should never happen with valid input)
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
