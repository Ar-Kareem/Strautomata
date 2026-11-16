
def policy(piles: list[int]) -> str:
    p = [int(x) for x in piles]

    def first_legal_move() -> str:
        for i, h in enumerate(p):
            if h > 0:
                return f"{i},1"
        # No legal move exists in a terminal position.
        return "0,0"

    # Terminal safety fallback.
    if all(h == 0 for h in p):
        return "0,0"

    ones = sum(1 for h in p if h == 1)
    big = [i for i, h in enumerate(p) if h > 1]

    # Case 1: all nonzero heaps are 1-heaps.
    if len(big) == 0:
        return first_legal_move()

    # Case 2: exactly one heap is bigger than 1.
    if len(big) == 1:
        i = big[0]
        h = p[i]
        target = 1 if (ones % 2 == 0) else 0
        take = h - target
        if 1 <= take <= h:
            return f"{i},{take}"
        return first_legal_move()

    # Case 3: at least two heaps are bigger than 1 -> normal Nim move.
    x = 0
    for h in p:
        x ^= h

    if x != 0:
        for i, h in enumerate(p):
            target = h ^ x
            if target < h:
                take = h - target
                if 1 <= take <= h:
                    return f"{i},{take}"

    # Losing position: return any legal move.
    return first_legal_move()
