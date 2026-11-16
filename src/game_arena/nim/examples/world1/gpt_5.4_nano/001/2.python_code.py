
def policy(piles: list[int]) -> str:
    # Misère Nim for 4 piles:
    # - If all nonzero piles are of size 1, take 1 from any pile.
    # - Else, play like normal Nim: move to a state with XOR = 0.
    nonzero = [(i, v) for i, v in enumerate(piles) if v > 0]
    if not nonzero:
        # No legal move should be possible in a valid game state.
        # Return a default legal move format; won't be reached in practice.
        return "0,1"

    ones_only = all(v == 1 for _, v in nonzero)
    if ones_only:
        # Take exactly 1 from any non-empty pile.
        i, _ = nonzero[0]
        return f"{i},1"

    # General case: there exists a pile > 1.
    x = 0
    for _, v in nonzero:
        x ^= v

    # If XOR is 0, current position is losing under optimal play.
    # Choose any legal move that changes the state (e.g., take 1 from a largest pile).
    if x == 0:
        i, v = max(nonzero, key=lambda t: t[1])
        return f"{i},1"

    # Otherwise find a pile to reduce so that the resulting XOR is 0.
    for i, v in nonzero:
        target = v ^ x
        # We need target < v to make a reduction.
        if target < v:
            take = v - target
            return f"{i},{take}"

    # Fallback (should not occur): take 1 from first non-empty pile.
    i, _ = nonzero[0]
    return f"{i},1"
