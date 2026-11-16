
def policy(piles):
    """
    Return the next move for misère Nim with four piles.

    Parameters
    ----------
    piles : list[int]
        List of length 4 containing the current pile sizes.

    Returns
    -------
    str
        A move in the format "pile,take" where `pile` is 0‑based and
        `take` is the number of objects removed from that pile.
    """
    # Helper: determine if a position is a losing (P) position for the player to move.
    def is_losing(state):
        # Remove zero piles for the "all ones" test
        non_zero = [x for x in state if x > 0]
        # All piles are 0 or 1
        if all(x <= 1 for x in non_zero):
            # losing iff even number of 1‑piles
            return len(non_zero) % 2 == 0
        # Otherwise use normal Nim xor rule
        xor_val = 0
        for x in state:
            xor_val ^= x
        return xor_val == 0

    # Try to find a winning move (leads to a losing position for opponent)
    for i, pile in enumerate(piles):
        if pile == 0:
            continue
        for take in range(1, pile + 1):
            new_state = piles.copy()
            new_state[i] -= take
            if is_losing(new_state):
                return f"{i},{take}"

    # No winning move found – we are in a losing position.
    # Return any legal move (first available).
    for i, pile in enumerate(piles):
        if pile > 0:
            return f"{i},1"

    # Should never reach here (all piles zero). Return a dummy move to keep the API contract.
    return "0,0"
