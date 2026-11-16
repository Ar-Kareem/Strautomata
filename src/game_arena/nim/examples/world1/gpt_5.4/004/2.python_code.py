
def policy(piles: list[int]) -> str:
    # Defensive handling: always return a legal move if one exists.
    # If somehow called on terminal state, return a syntactically valid fallback.
    if not isinstance(piles, list) or len(piles) != 4:
        return "0,1"

    nonzero = [(i, p) for i, p in enumerate(piles) if p > 0]

    # Terminal fallback; arena should not call policy here, but keep output valid.
    if not nonzero:
        return "0,1"

    # Misère Nim special case: all nonzero piles are size 1.
    if all(p == 1 for _, p in nonzero):
        k = len(nonzero)
        # Winning move: leave an even number of 1-heaps to opponent.
        # So if k is odd, remove one entire heap.
        # If k is even, no winning move exists; remove one legally.
        i = nonzero[0][0]
        return f"{i},1"

    # General case: same as normal Nim.
    x = 0
    for p in piles:
        x ^= p

    if x != 0:
        for i, p in enumerate(piles):
            target = p ^ x
            if target < p:
                take = p - target
                if take >= 1:
                    return f"{i},{take}"

    # If nim-sum is zero, no winning move under perfect play.
    # Return any legal move.
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"

    # Unreachable if there was a legal move.
    return "0,1"
