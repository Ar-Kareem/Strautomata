
def _first_legal_move(piles: list[int]) -> tuple[int, int]:
    for i, h in enumerate(piles):
        if h > 0:
            return i, 1
    # Terminal state: no legal move exists. The arena should not call policy here.
    return 0, 1


def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misère Nim:
    the player who takes the last object loses.
    Returns a move as 'pile,take'.
    """
    ones = 0
    bigs = []
    x = 0

    for i, h in enumerate(piles):
        x ^= h
        if h == 1:
            ones += 1
        elif h > 1:
            bigs.append(i)

    # Case 1: all nonzero piles are size 1.
    # Winning iff the number of 1-piles is even; in either case, removing any 1 is optimal/legal.
    if not bigs:
        i, take = _first_legal_move(piles)
        return f"{i},{take}"

    # Case 2: exactly one pile is bigger than 1.
    # Leave the opponent an odd number of 1-piles.
    if len(bigs) == 1:
        i = bigs[0]
        h = piles[i]
        if ones % 2 == 0:
            take = h - 1  # leave 1
        else:
            take = h      # remove the whole pile
        return f"{i},{take}"

    # Case 3: at least two big piles.
    # Play normal Nim: move to xor == 0 whenever possible.
    if x != 0:
        for i, h in enumerate(piles):
            target = h ^ x
            if target < h:
                take = h - target
                return f"{i},{take}"

        # Defensive fallback; should never be reached when x != 0.
        i, take = _first_legal_move(piles)
        return f"{i},{take}"

    # Losing position under perfect play (xor == 0 with at least two big piles).
    # Any legal move loses against perfect opposition, so use a deterministic trap heuristic.

    # If there are exactly two big piles, leave a one-big-pile state with an even number of 1s.
    # That often forces a less obvious misère response from the opponent.
    if len(bigs) == 2:
        i = min(bigs, key=lambda j: (piles[j], j))  # reduce the smaller big pile
        target = 0 if ones % 2 == 0 else 1
        take = piles[i] - target
        return f"{i},{take}"

    # Otherwise, reduce the smallest big pile to 1.
    i = min(bigs, key=lambda j: (piles[j], j))
    take = piles[i] - 1
    return f"{i},{take}"
