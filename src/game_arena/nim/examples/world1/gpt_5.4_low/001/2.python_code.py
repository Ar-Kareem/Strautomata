
def policy(piles: list[int]) -> str:
    # Guaranteed legal fallback: take 1 from the first nonempty pile.
    def fallback():
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
        # Terminal position should normally not be queried.
        return "0,1"

    nonzero = [(i, p) for i, p in enumerate(piles) if p > 0]
    if not nonzero:
        return fallback()

    ones = [i for i, p in nonzero if p == 1]
    bigs = [(i, p) for i, p in nonzero if p > 1]

    # Case 1: all nonempty piles are size 1
    if len(bigs) == 0:
        # Remove one whole heap (the only legal type of move here).
        # This is optimal because it leaves odd count to opponent when possible.
        return f"{ones[0]},1"

    # Case 2: exactly one pile > 1
    if len(bigs) == 1:
        big_i, big_p = bigs[0]
        one_count = len(ones)

        # Leave an odd number of 1-heaps to the opponent.
        if one_count % 2 == 0:
            # Reduce big heap to 1
            take = big_p - 1
            if take >= 1:
                return f"{big_i},{take}"
        else:
            # Remove big heap entirely
            take = big_p
            return f"{big_i},{take}"

        return fallback()

    # Case 3: at least two piles > 1 -> normal Nim move
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

    # If xor is already 0, this is a losing position with perfect play.
    # Still return a legal move.
    return fallback()
