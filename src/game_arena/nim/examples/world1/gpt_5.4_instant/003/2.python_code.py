
def policy(piles: list[int]) -> str:
    # Always return a legal move string "pile,take".
    # Misère Nim for 4 piles: player taking the last object loses.

    # Fallback legal move helper
    def first_legal():
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
        return "0,0"  # unreachable in a valid nonterminal call

    nonzero = [(i, p) for i, p in enumerate(piles) if p > 0]
    if not nonzero:
        return "0,0"  # terminal fallback; should not be queried

    ones = sum(1 for _, p in nonzero if p == 1)
    bigs = [(i, p) for i, p in nonzero if p > 1]

    # Case 1: all nonzero heaps are size 1
    if len(bigs) == 0:
        # Leave an odd number of 1-heaps to opponent if possible
        # If count is even, remove one whole heap.
        # If count is odd, no winning move exists; still play legally.
        i, _ = nonzero[0]
        return f"{i},1"

    # Case 2: exactly one heap > 1
    if len(bigs) == 1:
        i, p = bigs[0]
        # Leave opponent with odd number of 1-heaps total.
        # If ones is even -> reduce big heap to 0
        # If ones is odd  -> reduce big heap to 1
        target = 0 if ones % 2 == 0 else 1
        take = p - target
        if 1 <= take <= p:
            return f"{i},{take}"
        return first_legal()

    # Case 3: at least two heaps > 1 -> same move rule as normal Nim
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

    # Losing position or safety fallback: return any legal move
    return first_legal()
