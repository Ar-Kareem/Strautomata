
def policy(piles: list[int]) -> str:
    """
    Chooses the optimal move in a Nim game (4 piles) with misère rule.

    Args:
        piles: A list of integers representing the number of objects in each pile.

    Returns:
        A string representing the move in the format 'pile,take'.
    """
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile

    if nim_sum != 0:
        # Winning position: try to make nim_sum zero
        for i in range(4):
            target_size = piles[i] ^ nim_sum
            if target_size < piles[i]:
                take = piles[i] - target_size
                return f"{i},{take}"

        # If we reach here, it means reducing any pile to nim_sum XOR piles[i]
        # will make it *larger*. Which will never happen. This means we are already in
        # in a state that nim_sum is non-zero but turning nim_sum to zero will result
        # in pile size larger than original. Take 1 in the biggest pile.
        max_pile = 0
        max_size = 0
        for i in range(4):
            if piles[i] > max_size:
                max_size = piles[i]
                max_pile = i
        return f"{max_pile},1"

    else:
        # Losing position: try to make nim_sum non-zero, avoid taking the last object
        # Endgame handling: if only piles of size 1 remain, leave an even number
        ones = 0
        non_ones = 0
        for pile in piles:
            if pile == 1:
                ones += 1
            elif pile > 1:
                non_ones += 1

        if non_ones == 0: #only piles of size 1 left.
            if ones % 2 == 0: #losing position, but can force to lose a single pile
                for i in range(4):
                    if piles[i] != 0:
                        return f"{i},1"

        # Try to take from the largest pile as much as possible to avoid
        # creating piles of size 1 if other piles are greater than 1
        max_pile = -1
        max_size = 0
        for i in range(4):
            if piles[i] > max_size:
                max_size = piles[i]
                max_pile = i

        if max_pile != -1:
            if piles[max_pile] > 1:
                return f"{max_pile},1"
                
        # all sizes are 1, force to lose the game
        for i in range(4):
            if piles[i] != 0:
                return f"{i},1"
                
        # If we are here, it means the game is over and all piles are zero which is impossible.
        return "0,1"
