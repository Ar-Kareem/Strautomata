
def policy(piles: list[int]) -> str:
    # Legal fallback in case anything unexpected happens
    def fallback():
        for i, x in enumerate(piles):
            if x > 0:
                return f"{i},1"
        return "0,0"  # unreachable in valid nonterminal play

    try:
        nonzero = [x for x in piles if x > 0]
        if not nonzero:
            return fallback()

        # Misère special case: all nonzero piles are size 1
        if all(x == 1 for x in nonzero):
            k = len(nonzero)
            # Want to leave an odd number of 1-heaps to opponent.
            # If k is even, remove one whole heap -> k-1 odd.
            # If k is odd, any move loses eventually; remove one heap anyway.
            for i, x in enumerate(piles):
                if x > 0:
                    return f"{i},1"

        # General case: play like normal Nim, make xor-sum zero
        xorsum = 0
        for x in piles:
            xorsum ^= x

        if xorsum != 0:
            for i, x in enumerate(piles):
                target = x ^ xorsum
                if target < x:
                    take = x - target
                    if 1 <= take <= x:
                        return f"{i},{take}"

        # If xor is already zero, no winning move exists under perfect play.
        # Choose a sensible legal move:
        # Prefer reducing a pile > 1 down to 1 to avoid bad all-ones transitions.
        for i, x in enumerate(piles):
            if x > 1:
                return f"{i},{x - 1}"

        return fallback()

    except Exception:
        return fallback()
