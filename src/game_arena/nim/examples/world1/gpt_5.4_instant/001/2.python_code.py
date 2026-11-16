
def policy(piles: list[int]) -> str:
    # Always return a legal move string: "pile,take"
    # Misère Nim for 4 piles: player taking the last object loses.

    # Collect nonzero piles and basic stats
    nonzero_indices = [i for i, x in enumerate(piles) if x > 0]

    # Fallback safety: if somehow terminal, still emit a syntactically valid string.
    # Arena should not call on terminal states, but keep behavior defined.
    if not nonzero_indices:
        return "0,0"

    ones = sum(1 for x in piles if x == 1)
    big = [(i, x) for i, x in enumerate(piles) if x > 1]
    nonzero_count = len(nonzero_indices)

    # Case 1: all nonzero piles are size 1
    if len(big) == 0:
        # Winning if even number of 1-piles: remove one whole pile, leaving odd count.
        # If odd, no winning move exists; any legal move is fine.
        i = nonzero_indices[0]
        return f"{i},1"

    # Case 2: exactly one pile > 1
    if len(big) == 1:
        i, x = big[0]
        # Let k be number of 1-piles.
        # Optimal misère rule:
        # - if k even, reduce big pile to 1
        # - if k odd, reduce big pile to 0
        if ones % 2 == 0:
            take = x - 1
            if take >= 1:
                return f"{i},{take}"
        else:
            take = x
            return f"{i},{take}"

    # Case 3: at least two piles > 1 -> play normal Nim
    xor_sum = 0
    for x in piles:
        xor_sum ^= x

    if xor_sum != 0:
        for i, x in enumerate(piles):
            target = x ^ xor_sum
            if target < x:
                take = x - target
                if 1 <= take <= x:
                    return f"{i},{take}"

    # If xor_sum == 0, this is a losing position under perfect play.
    # Return any legal move.
    i = nonzero_indices[0]
    return f"{i},1"
