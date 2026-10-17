
def policy(piles: list[int]) -> str:
    # Defensive normalization
    if not isinstance(piles, list) or len(piles) != 4:
        return "0,1"

    # Ensure integers and nonnegative handling for robustness
    p = []
    for x in piles:
        try:
            v = int(x)
        except Exception:
            v = 0
        if v < 0:
            v = 0
        p.append(v)

    # Legal fallback: remove 1 from first nonempty pile
    def fallback():
        for i, x in enumerate(p):
            if x > 0:
                return f"{i},1"
        return "0,1"  # Should never occur in a valid nonterminal call

    nonzero = [(i, x) for i, x in enumerate(p) if x > 0]
    if not nonzero:
        return "0,1"

    ones = sum(1 for x in p if x == 1)
    big = [(i, x) for i, x in enumerate(p) if x > 1]
    nonzero_count = len(nonzero)

    # Misère Nim special case: all nonzero piles are size 1
    if ones == nonzero_count:
        # Winning move: leave odd number of 1-heaps to opponent
        # If count is even, remove one whole heap.
        # If count is odd, position is losing; make any legal move.
        i = nonzero[0][0]
        return f"{i},1"

    # Misère Nim special case: exactly one pile > 1
    if len(big) == 1:
        i, x = big[0]
        k = ones  # number of 1-heaps besides this big pile

        # Reduce big pile so that only 1-heaps remain and opponent sees odd count
        # If we leave t stones in the big pile (t is 0 or 1), opponent sees k+t heaps of 1.
        # We want k+t odd.
        target = 1 if k % 2 == 0 else 0  # choose t so k+t is odd
        take = x - target
        if 1 <= take <= x:
            return f"{i},{take}"
        return fallback()

    # General case: play normal Nim move to make xor zero
    xor_sum = 0
    for x in p:
        xor_sum ^= x

    if xor_sum != 0:
        for i, x in enumerate(p):
            target = x ^ xor_sum
            if target < x:
                take = x - target
                if 1 <= take <= x:
                    return f"{i},{take}"

    # If xor is already 0 (losing position), make any legal move
    return fallback()
