
def policy(piles: list[int]) -> str:
    # Misère Nim (4 piles): player who takes the last object loses.
    # Optimal strategy:
    # - If all non-empty piles have size 1: remove exactly 1 from any pile.
    # - Otherwise: play like normal Nim aiming for XOR = 0.
    #   Find a pile where changing it to make XOR zero is possible.

    # Ensure we have exactly 4 piles (game spec), but don't hard-fail.
    if len(piles) != 4:
        # Fall back to a legal move: take 1 from the first non-empty pile.
        for i, x in enumerate(piles):
            if x > 0:
                return f"{i},1"
        return "0,0"  # Should never happen in valid arena states.

    # Gather indices of non-empty piles
    non_empty = [i for i, x in enumerate(piles) if x > 0]

    # If all piles are empty, no legal move; shouldn't occur.
    if not non_empty:
        return "0,0"

    # Check special misère condition: all non-empty piles are size 1
    if all(piles[i] == 1 for i in non_empty):
        # Remove exactly one from any non-empty pile.
        i = non_empty[0]
        return f"{i},1"

    # General case: normal Nim move to make XOR zero
    x = 0
    for v in piles:
        x ^= v

    # If XOR already zero, any move can be losing; but we still must return legal.
    # We'll use a fallback that tries to reduce a largest pile by 1.
    if x == 0:
        # Pick a non-empty pile with maximum size; take 1
        i = max(non_empty, key=lambda k: piles[k])
        return f"{i},1"

    # Otherwise find pile i such that (piles[i] XOR x) < piles[i]
    for i in non_empty:
        vi = piles[i]
        target = vi ^ x
        if target < vi:
            take = vi - target
            if 1 <= take <= vi:
                return f"{i},{take}"

    # Fallback (shouldn't happen): take 1 from largest non-empty pile
    i = max(non_empty, key=lambda k: piles[k])
    return f"{i},1"
