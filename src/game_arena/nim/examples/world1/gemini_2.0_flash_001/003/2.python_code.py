
def policy(piles: list[int]) -> str:
    """
    A smart Nim policy that attempts to make the nim-sum zero on each move.
    Handles the special case when only piles of size one remain.
    """
    nim_sum = 0
    for pile_size in piles:
        nim_sum ^= pile_size

    if nim_sum == 0:
        # Losing position, try to make a move that might confuse the opponent or prolong the game
        for i in range(4):
            if piles[i] > 1:
                return f"{i},{piles[i] - 1}"

        # If all piles have at most 1 object, take one to force an odd number of piles with size 1
        count_ones = sum(1 for pile_size in piles if pile_size == 1)
        for i in range(4):
            if piles[i] > 0:
                if count_ones % 2 == 0:
                    return f"{i},1"
                else:
                    
                    remaining_ones = sum(1 for j in range(4) if j != i and piles[j] == 1)
                    if remaining_ones % 2 == 1:
                       return f"{i},1"
                    
                    #look for another move
                    for j in range(4):
                        if piles[j] > 0 and j != i:
                            return f"{j},1"
                    
                    return f"{i},1"  #fall back, should not happen
        return "0,0" # Should never happen

    else:
        # Winning position, make nim-sum zero
        for i in range(4):
            target_size = piles[i] ^ nim_sum
            if target_size < piles[i]:
                return f"{i},{piles[i] - target_size}"

        # Should not happen if nim_sum is non-zero and a valid move exists
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1" # Return a legal move, even if not optimal

        return "0,0" # Should never happen
