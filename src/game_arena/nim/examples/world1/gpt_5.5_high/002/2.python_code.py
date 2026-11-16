
def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misere Nim.

    Move format: "pile,take"
    Misere rule: the player who takes the last object loses.
    """

    def first_legal() -> str:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
        # No legal move exists in a terminal state; arena should not call policy then.
        return "0,0"

    def safe_move(i: int, take: int) -> str:
        if 0 <= i < len(piles) and 1 <= take <= piles[i]:
            return f"{i},{take}"
        return first_legal()

    n = len(piles)
    if n != 4:
        # Defensive fallback, though the arena promises length 4.
        return first_legal()

    nonzero = [i for i, p in enumerate(piles) if p > 0]
    if not nonzero:
        return "0,0"

    ones = sum(1 for p in piles if p == 1)
    big = [i for i, p in enumerate(piles) if p > 1]

    # Endgame: all non-empty piles are size 1.
    # If there is an even number of 1-piles this is winning; otherwise losing,
    # but the only legal kind of move is still to remove one 1.
    if not big:
        return first_legal()

    # Special misere case: exactly one pile larger than 1.
    # Move so the opponent receives an odd number of 1-piles, which is losing.
    if len(big) == 1:
        i = big[0]
        h = piles[i]

        if ones % 2 == 0:
            # Leave this large pile as a single 1.
            # Opponent faces odd number of ones.
            return safe_move(i, h - 1)
        else:
            # Remove the large pile completely.
            # Opponent faces odd number of ones.
            return safe_move(i, h)

    # General case: at least two piles larger than 1.
    # Misere Nim is played like normal Nim here: move to xor zero if possible.
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    if xor_sum != 0:
        for i, p in enumerate(piles):
            target = p ^ xor_sum
            if target < p:
                return safe_move(i, p - target)

    # Losing position under perfect play: xor is already zero.
    # Any legal move loses against perfect play, but choose a move that can
    # create awkward misere endgames for weaker normal-Nim opponents.
    if len(big) == 2:
        # Leave exactly one large pile, a common trap for normal-Nim policies.
        i = min(big, key=lambda j: piles[j])
        return safe_move(i, piles[i])

    # With three or four large piles, reduce the smallest large pile to 1.
    i = min(big, key=lambda j: piles[j])
    return safe_move(i, piles[i] - 1)
