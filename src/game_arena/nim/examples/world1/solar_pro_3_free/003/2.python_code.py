
def policy(piles: list[int]) -> str:
    """
    Optimal misère Nim move for a game with 4 piles.
    Returns a string ``pile,take`` where ``pile`` is 0‑based and ``take`` is a positive amount
    that can be removed from that pile.
    """
    # Defensive guard – the arena never calls this on a finished board,
    # but handle the case gracefully.
    if all(p == 0 for p in piles):
        raise ValueError("No legal move – the board is empty")

    # Helper to find the index of a pile where we want to act.
    def find_one(piles: list[int], condition) -> int:
        for i, p in enumerate(piles):
            if condition(p):
                return i
        raise RuntimeError("Unexpected: no pile satisfying condition")

    # 1. All piles are size 0 or 1 only (no heap >1)
    ones = [p for p in piles if p > 0]
    if all(p == 1 for p in ones):
        # Only size‑1 piles exist – parity decides the outcome.
        idx = find_one(piles, lambda p: p == 1)
        return f"{idx},1"

    # 2. There is at least one pile larger than 1.
    # Compute the normal Nim xor.
    xor = 0
    for p in piles:
        xor ^= p

    # Winning case: xor != 0.
    if xor != 0:
        # Find a pile that can be reduced to xor (i.e. size_i > xor).
        candidate = find_one(piles, lambda p: p > xor)
        if candidate is not None:
            take = piles[candidate] - xor
            return f"{candidate},{take}"
        # No pile larger than xor – this can happen only when there is
        # exactly one pile >1 and the rest are size‑1 piles.
        # Count the size‑1 piles.
        cnt_ones = sum(1 for p in piles if p == 1)
        big_idx = find_one(piles, lambda p: p > 1)
        if cnt_ones % 2 == 0:
            # Even number of ones – reduce the big pile to size 1.
            take = piles[big_idx] - 1
            return f"{big_idx},{take}"
        else:
            # Odd number of ones – take the whole big pile.
            take = piles[big_idx]
            return f"{big_idx},{take}"

    # 3. xor == 0 – losing position (P‑position).
    # Any legal move is acceptable; we try to keep the opponent in a losing spot.
    # Prefer to take from the largest pile, unless it is the only pile and we
    # would take the last object (which loses). In that case just take 1.
    largest = max(piles)
    # If there is a unique non‑zero pile, taking it would be losing,
    # so we take only one token (leaving the opponent forced to take the last).
    if len([p for p in piles if p > 0]) == 1:
        idx = find_one(piles, lambda p: p > 0)
        return f"{idx},1"
    else:
        # Otherwise, take all from the largest pile (or at least one token).
        idx = find_one(piles, lambda p: p == largest)
        take = piles[idx]
        # If taking the whole pile would be the last object (i.e. after removal
        # there is only one pile left and we would be the one who took it),
        # we keep one object instead.
        if sum(p == 0 for p in piles) + (sum(p == largest for p in piles) - 1) == len(piles) - 1:
            # Removing this pile would be the final move → we avoid that.
            take = 1
        return f"{idx},{take}"
