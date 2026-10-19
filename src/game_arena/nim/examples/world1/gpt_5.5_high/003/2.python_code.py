
def policy(piles: list[int]) -> str:
    """
    Perfect-play policy for 4-pile misere Nim.
    Return format: 'pile,take'
    """

    # Find any legal move first, for safe fallback.
    first_nonempty = -1
    for i, h in enumerate(piles):
        if h > 0:
            first_nonempty = i
            break

    # Terminal states should not be queried; no legal move exists here.
    if first_nonempty == -1:
        return "0,0"

    ones = 0
    big = []

    for i, h in enumerate(piles):
        if h == 1:
            ones += 1
        elif h > 1:
            big.append(i)

    # Case 1: all non-empty piles are size 1.
    # Only legal move is to remove 1 from some pile.
    if len(big) == 0:
        return f"{first_nonempty},1"

    # Case 2: exactly one pile is bigger than 1.
    # Leave the opponent an odd number of 1-piles, which is losing in misere Nim.
    if len(big) == 1:
        i = big[0]
        h = piles[i]

        if ones % 2 == 0:
            # Leave this big pile as a single 1.
            take = h - 1
        else:
            # Remove this pile completely.
            take = h

        return f"{i},{take}"

    # Case 3: at least two piles are bigger than 1.
    # Use normal Nim strategy: move to xor 0 if possible.
    nim_xor = 0
    for h in piles:
        nim_xor ^= h

    if nim_xor != 0:
        for i, h in enumerate(piles):
            target = h ^ nim_xor
            if target < h:
                take = h - target
                return f"{i},{take}"

    # Losing position under perfect play: xor is already 0 with multiple big piles.
    # Any move loses against perfect play, so choose a simple legal move.
    largest_i = max(range(len(piles)), key=lambda j: piles[j])
    return f"{largest_i},1"
