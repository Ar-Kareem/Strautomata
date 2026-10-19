
def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misere Nim.

    Move format: 'pile,take'
    Rule: player who takes the last object loses.
    """

    # Terminal positions should not be passed to the policy.
    # There is no legal move if all piles are zero, but return a formatted fallback.
    if not any(p > 0 for p in piles):
        return "0,0"

    big = [i for i, p in enumerate(piles) if p > 1]
    ones = sum(1 for p in piles if p == 1)

    # Case 1: all remaining piles are size 0 or 1.
    # With k one-piles, the player to move wins iff k is even.
    # The winning move is to remove one object, leaving odd k to opponent.
    if len(big) == 0:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"

    # Case 2: exactly one pile is larger than 1.
    # Reduce it to leave an odd number of one-piles to the opponent.
    if len(big) == 1:
        i = big[0]
        h = piles[i]

        if ones % 2 == 0:
            # Leave this big pile as a single 1-pile.
            # ones + 1 becomes odd.
            return f"{i},{h - 1}"
        else:
            # Remove the whole big pile.
            # ones remains odd.
            return f"{i},{h}"

    # Case 3: at least two piles are larger than 1.
    # Normal Nim xor strategy is optimal in this region.
    nim_sum = 0
    for p in piles:
        nim_sum ^= p

    if nim_sum != 0:
        for i, h in enumerate(piles):
            target = h ^ nim_sum
            if target < h:
                take = h - target
                return f"{i},{take}"

    # Losing position under perfect play.
    # Any legal move loses against an optimal opponent; choose a safe legal move.
    largest = max(range(len(piles)), key=lambda i: piles[i])
    if piles[largest] > 0:
        return f"{largest},1"

    # Extra fallback, should never be reached for a nonterminal legal state.
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"

    return "0,0"
