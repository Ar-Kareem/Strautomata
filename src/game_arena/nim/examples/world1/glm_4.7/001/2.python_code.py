
def policy(piles):
    # Count ones and check whether all piles are 0 or 1
    ones = piles.count(1)
    all_small = all(p <= 1 for p in piles)

    if all_small:
        # Only moves are taking a whole pile of size 1.
        for i, p in enumerate(piles):
            if p == 1:
                return f"{i},1"
        # Should never be called on an all‑zero position.
        return "0,1"   # fallback, but input is guaranteed non‑terminal

    # There is at least one pile with size >= 2
    x = 0
    for p in piles:
        x ^= p

    if x == 0:
        # Losing position – any legal move is acceptable.
        for i, p in enumerate(piles):
            if p >= 2:
                return f"{i},1"
        # Fallback (should not happen because we are not all_small)
        return "0,1"

    # Winning position (x != 0)
    # Try a normal Nim move that leaves at least one pile >= 2.
    for i, p in enumerate(piles):
        new_size = p ^ x
        if new_size < p:   # this would reduce the pile
            new_piles = piles.copy()
            new_piles[i] = new_size
            if any(q >= 2 for q in new_piles):
                take = p - new_size
                return f"{i},{take}"

    # Special case: exactly one pile > 1 and all others are 0 or 1.
    # Find that pile and the number of ones.
    big_idx = None
    big_val = 0
    ones = 0
    for i, p in enumerate(piles):
        if p > 1:
            big_idx = i
            big_val = p
        elif p == 1:
            ones += 1

    # Leave an odd number of ones.
    if ones % 2 == 1:
        take = big_val          # take everything, leave 0
    else:
        take = big_val - 1      # leave 1
    return f"{big_idx},{take}"
