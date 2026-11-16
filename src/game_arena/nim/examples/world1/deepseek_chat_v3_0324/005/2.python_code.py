
def policy(piles: list[int]) -> str:
    # Calculate nim-sum
    nim_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
    
    all_one = all(pile <= 1 for pile in piles)
    
    if nim_sum == 0:
        # All piles are 1 - misère Nim strategy
        if all_one:
            non_empty_piles = [i for i, pile in enumerate(piles) if pile > 0]
            if len(non_empty_piles) % 2 == 1:
                # Take all from the first non-empty pile
                pile = non_empty_piles[0]
                take = piles[pile]
            else:
                # Leave 1 object (take all but one)
                pile = non_empty_piles[0]
                take = piles[pile] - 1
            return f"{pile},{take}"
        else:
            # Take from the largest pile
            max_pile = max((pile, i) for i, pile in enumerate(piles))[1]
            take = max(piles[max_pile] - 1, 1)  # Try to leave 1 if taking all would make all piles 1
            return f"{max_pile},{take}"
    else:
        # Find a move that makes nim-sum zero
        for i, pile in enumerate(piles):
            target = pile ^ nim_sum
            if target < pile:
                take = pile - target
                return f"{i},{take}"
    
    # Fallback (should never be reached with proper implementation)
    for i, pile in enumerate(piles):
        if pile > 0:
            return f"{i},1"
    return "0,0"  # Should never reach here
