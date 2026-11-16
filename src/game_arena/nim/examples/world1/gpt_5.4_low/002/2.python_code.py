
def policy(piles: list[int]) -> str:
    # Safety: always return a legal move if any exists.
    nonzero_indices = [i for i, p in enumerate(piles) if p > 0]
    if not nonzero_indices:
        # Terminal state should normally not be queried, but stay robust.
        return "0,0"

    ones = sum(1 for p in piles if p == 1)
    bigs = [(i, p) for i, p in enumerate(piles) if p > 1]
    nonzero = len(nonzero_indices)

    # Case 1: all nonempty piles are size 1
    if len(bigs) == 0:
        # Winning iff even number of 1-heaps; remove one whole heap.
        i = nonzero_indices[0]
        return f"{i},1"

    # Case 2: exactly one pile > 1
    if len(bigs) == 1:
        i, p = bigs[0]
        # Leave opponent an odd number of 1-heaps.
        target = 1 if (ones % 2 == 0) else 0
        take = p - target
        if take >= 1:
            return f"{i},{take}"
        # Fallback, though take should always be >= 1 here.
        return f"{i},1"

    # Case 3: at least two piles > 1 -> normal Nim strategy
    x = 0
    for p in piles:
        x ^= p

    if x != 0:
        for i, p in enumerate(piles):
            target = p ^ x
            if target < p:
                take = p - target
                if 1 <= take <= p:
                    return f"{i},{take}"

    # Losing position under perfect play: return any legal move.
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"

    # Unreachable fallback
    return "0,0"
