
def _legal_fallback(piles: list[int]) -> str:
    """Return a legal move for any non-terminal position."""
    best_i = -1
    best_p = 0
    for i, p in enumerate(piles):
        if p > best_p:
            best_i = i
            best_p = p

    if best_i >= 0 and best_p > 0:
        return f"{best_i},1"

    # Terminal position: no legal move exists. This should not be called by the arena.
    return "0,0"


def policy(piles: list[int]) -> str:
    """
    Perfect-play policy for 4-pile misere Nim.
    Move format: 'pile,take'.
    """

    ones = sum(1 for p in piles if p == 1)
    large_indices = [i for i, p in enumerate(piles) if p > 1]
    large_count = len(large_indices)

    # Case 1: all remaining non-empty piles are singletons.
    # With an even number of singletons this is winning; with odd it is losing,
    # but the only kind of legal move is still to take one singleton.
    if large_count == 0:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
        return "0,0"

    # Case 2: exactly one pile has size > 1.
    # Move to an odd number of singleton piles for the opponent.
    if large_count == 1:
        i = large_indices[0]
        p = piles[i]

        if ones % 2 == 0:
            # Leave this large pile as a singleton.
            take = p - 1
        else:
            # Remove the large pile entirely.
            take = p

        return f"{i},{take}"

    # Case 3: at least two piles are larger than 1.
    # Misere Nim is equivalent to normal Nim here: move to xor zero if possible.
    nim_sum = 0
    for p in piles:
        nim_sum ^= p

    if nim_sum != 0:
        for i, p in enumerate(piles):
            target = p ^ nim_sum
            if target < p:
                take = p - target
                return f"{i},{take}"

    # Losing position under perfect play; no winning move exists.
    # Return a simple legal move.
    return _legal_fallback(piles)
