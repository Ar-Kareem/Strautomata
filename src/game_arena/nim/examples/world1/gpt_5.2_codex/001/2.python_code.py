
def policy(piles: list[int]) -> str:
    # Misère Nim strategy for 4 piles
    # Ensure we always return a legal move
    if sum(piles) == 0:
        return "0,0"  # should not be called in terminal state

    max_pile = max(piles)
    # Count heaps
    nonzero_indices = [i for i, p in enumerate(piles) if p > 0]
    count_nonzero = len(nonzero_indices)
    count_ones = sum(1 for p in piles if p == 1)
    count_big = sum(1 for p in piles if p > 1)

    # Case 1: all heaps are size 1 (or 0)
    if max_pile <= 1:
        # If count_nonzero is even, take one to leave odd; otherwise just take one
        # Any move removes exactly one heap
        i = nonzero_indices[0]
        return f"{i},1"

    # Case 2: exactly one heap > 1
    if count_big == 1:
        big_index = next(i for i, p in enumerate(piles) if p > 1)
        big_size = piles[big_index]
        if count_ones % 2 == 0:
            # leave one in the big heap
            take = big_size - 1
        else:
            # take all from the big heap
            take = big_size
        return f"{big_index},{take}"

    # Case 3: normal Nim play (nim-sum strategy)
    nim_sum = 0
    for p in piles:
        nim_sum ^= p

    if nim_sum == 0:
        # Losing position; take 1 from first non-zero pile
        i = nonzero_indices[0]
        return f"{i},1"

    # Find a move to make nim-sum zero
    for i, p in enumerate(piles):
        target = p ^ nim_sum
        if target < p:
            take = p - target
            return f"{i},{take}"

    # Fallback (should never happen)
    i = nonzero_indices[0]
    return f"{i},1"
