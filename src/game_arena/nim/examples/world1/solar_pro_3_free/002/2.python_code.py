
def policy(piles: list[int]) -> str:
    """
    Perfect misère Nim policy for 4 piles.
    Returns a legal move as \"pile,take\" where pile is 0‑based and take>=1.
    """
    # Sanity checks
    if len(piles) != 4 or any(p < 0 for p in piles):
        raise ValueError("Invalid input")

    # Helper to copy and modify a specific pile
    def try_move(pile_idx: int, new_size: int) -> str:
        take = piles[pile_idx] - new_size
        # Ensure the move is legal
        assert 1 <= take <= piles[pile_idx]
        return f"{pile_idx},{take}"

    # Count of piles that contain exactly one stone
    ones = sum(1 for p in piles if p == 1)

    # Compute the Nim‑sum (XOR of all pile sizes)
    xor = 0
    for p in piles:
        xor ^= p

    # -----------------------------------------------------------------
    # Case 1: Nim‑sum is zero
    if xor == 0:
        # Is there any heap larger than one?
        big_exists = any(p > 1 for p in piles)

        if big_exists:
            # Reduce a big heap to size 1 (taking all but one stone)
            for i, p in enumerate(piles):
                if p > 1:
                    return try_move(i, 1)   # take all but one
        else:
            # All piles are 0 or 1 and the XOR is zero → even number of 1‑piles
            # Take a whole 1‑pile to make the count odd (winning move)
            for i, p in enumerate(piles):
                if p == 1:
                    return try_move(i, 0)   # take the whole pile (size 1)
            # Fallback: all piles are zero (terminal); shouldn't happen in a legal game
            return "0,0"
        return ""  # unreachable

    # -----------------------------------------------------------------
    # Case 2: Nim‑sum is non‑zero
    # If there is no heap larger than one, the only legal moves are to take a whole 1‑pile.
    if not any(p > 1 for p in piles):
        # e.g. [1,1,1] (odd count) → losing position; any legal move is fine.
        for i, p in enumerate(piles):
            if p == 1:
                return try_move(i, 0)
        return ""  # unreachable

    # There is at least one heap > 1 and xor != 0 → winning position.
    # Look for a normal Nim move that makes xor zero and leaves a heap > 1.
    for i, p in enumerate(piles):
        if p == 0:
            continue
        new_size = p ^ xor
        if new_size < p:               # a genuine reduction
            # Build the candidate position
            cand = list(piles)
            cand[i] = new_size
            # Does it still contain a heap larger than one?
            if any(c > 1 for c in cand):
                return try_move(i, new_size)

            # Otherwise all piles are ≤ 1 after the move.
            # Count the 1‑stones in the candidate position.
            cand_ones = sum(1 for c in cand if c == 1)

            if cand_ones % 2 == 1:    # odd number of 1‑stones → P‑position
                return try_move(i, new_size)

            # The candidate move would give the opponent an even number of 1‑piles,
            # so we adjust the move to obtain an odd count.
            # If the target size is 0, we instead reduce to 1 (add a 1).
            # If the target size is 1, we instead remove the whole pile (to 0).
            if new_size == 0:
                # Removing the whole pile keeps the parity unchanged
                if ones % 2 == 1:
                    return try_move(i, 0)   # take whole heap
                else:
                    # We need to add a 1 → reduce to size 1
                    return try_move(i, p - 1)
            else:  # new_size == 1 (the only other ≤1 possibility)
                # Adding a 1 would make an even count; better to remove whole heap
                if ones % 2 == 1:
                    # removing the whole heap leaves odd count
                    return try_move(i, p)
                else:
                    # removing whole heap leaves even count, so add a 1
                    return try_move(i, p - 1)

    # -----------------------------------------------------------------
    # If we reach here, no normal Nim move led to a P‑position.
    # Fallback: reduce the first big heap to 1 (the safest losing move).
    for i, p in enumerate(piles):
        if p > 1:
            return try_move(i, 1)
    # This line is theoretically unreachable because at least one big heap exists.
    return ""
