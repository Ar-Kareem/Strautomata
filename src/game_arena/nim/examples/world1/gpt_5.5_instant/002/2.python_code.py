
def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misere Nim:
    - Players remove >=1 from one pile.
    - Player taking the last object loses.
    Return format: "pile,take".
    """
    # Ensure we have usable integer pile sizes
    p = [int(x) if x is not None else 0 for x in piles]

    # Legal fallback: take 1 from the first non-empty pile.
    def fallback() -> str:
        for i, v in enumerate(p):
            if v > 0:
                return f"{i},1"
        # Terminal state should not be queried; return syntactically valid fallback.
        return "0,1"

    nonzero = [(i, v) for i, v in enumerate(p) if v > 0]
    if not nonzero:
        return fallback()

    ones = sum(1 for v in p if v == 1)
    bigs = [(i, v) for i, v in enumerate(p) if v > 1]
    b = len(bigs)

    # Endgame: only heaps of size 1 remain.
    # In misere play, you want your opponent to face an odd number of 1-heaps.
    # If current count is even, take 1 to leave odd (winning).
    # If current count is odd, every move is losing under perfect play; take 1 legally.
    if b == 0:
        return f"{nonzero[0][0]},1"

    # Special misere transition: exactly one heap bigger than 1.
    # Choose how much to remove from it so the opponent faces an odd number of 1-heaps.
    # If current number of 1-heaps is even, reduce big heap to 1 -> opponent sees odd ones.
    # If current number of 1-heaps is odd, remove the big heap entirely -> opponent sees odd ones.
    if b == 1:
        i, v = bigs[0]
        if ones % 2 == 0:
            take = v - 1
            if take >= 1:
                return f"{i},{take}"
            return fallback()
        else:
            return f"{i},{v}"

    # General case: at least two heaps bigger than 1.
    # Use normal Nim xor move when possible.
    x = 0
    for v in p:
        x ^= v

    if x != 0:
        for i, v in enumerate(p):
            target = v ^ x
            if target < v:
                take = v - target
                if 1 <= take <= v:
                    return f"{i},{take}"

    # If xor is zero, this is a losing position under perfect play.
    # Make a safe legal move: remove 1 from the smallest heap > 1 if possible,
    # otherwise from any non-empty heap.
    smallest_big = min(bigs, key=lambda t: t[1])
    return f"{smallest_big[0]},1"
