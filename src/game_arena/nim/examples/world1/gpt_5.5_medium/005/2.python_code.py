
def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misere Nim.
    Return format: 'pile,take'
    """

    # Terminal positions should not be queried by the arena.
    # There is no legal move when all piles are zero.
    if sum(piles) == 0:
        return "0,0"

    ones = sum(1 for p in piles if p == 1)
    big_indices = [i for i, p in enumerate(piles) if p > 1]

    # Case 1: all piles are 0 or 1.
    # In misere Nim, odd number of ones is losing, even is winning.
    # The only legal kind of move is to remove one whole pile.
    if not big_indices:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"

    # Case 2: exactly one pile has size greater than 1.
    # Choose whether to leave that pile as 0 or 1 so that the opponent
    # faces an odd number of singletons, which is losing.
    if len(big_indices) == 1:
        i = big_indices[0]
        pile_size = piles[i]

        if ones % 2 == 0:
            # Leave one more singleton: even + 1 = odd.
            desired_remaining = 1
        else:
            # Leave no singleton from this pile: odd remains odd.
            desired_remaining = 0

        take = pile_size - desired_remaining
        if 1 <= take <= pile_size:
            return f"{i},{take}"

    # Case 3: at least two piles are greater than 1.
    # Use the normal Nim xor strategy. This is also optimal in misere Nim
    # until the game reaches the one-big-pile or all-singletons endgame.
    nim_xor = 0
    for p in piles:
        nim_xor ^= p

    if nim_xor != 0:
        for i, p in enumerate(piles):
            target = p ^ nim_xor
            if target < p:
                take = p - target
                if 1 <= take <= p:
                    return f"{i},{take}"

    # If xor is zero with at least two big piles, this is a losing position
    # against perfect play. Return a simple legal move that keeps the game going.
    largest_index = max(range(len(piles)), key=lambda i: piles[i])
    if piles[largest_index] > 0:
        return f"{largest_index},1"

    # Safety fallback for any unexpected non-terminal input.
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"

    return "0,0"
