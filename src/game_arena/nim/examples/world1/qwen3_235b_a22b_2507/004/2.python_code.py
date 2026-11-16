
def policy(piles: list[int]) -> str:
    import numpy as np

    # Count piles with more than 1 stone
    big_piles = [i for i in range(4) if piles[i] > 1]
    ones = sum(1 for p in piles if p == 1)
    zeros = sum(1 for p in piles if p == 0)
    non_zero = 4 - zeros

    # Case 1: Only one pile has >1 stone
    if len(big_piles) == 1:
        big_idx = big_piles[0]
        # We want to control the parity of ones
        # If current ones are even, reduce big pile to 1 (so total non-zero is odd)
        # If ones is odd, reduce big pile to 0 (so total non-zero is even)
        if ones % 2 == 0:
            # Reduce big pile to 1 -> total ones becomes odd
            take = piles[big_idx] - 1
            if take >= 1:
                return f"{big_idx},{take}"
            else:
                # Already 1? Shouldn't happen.
                # Fall through
                pass
        else:
            # Reduce big pile to 0
            take = piles[big_idx]
            if take >= 1:
                return f"{big_idx},{take}"

    # Case 2: No pile has more than 1 stone (only 0s and 1s)
    if len(big_piles) == 0:
        # Take from any pile with 1
        for i in range(4):
            if piles[i] == 1:
                return f"{i},1"

    # Case 3: Two or more piles have >1 stone -> play normal Nim
    xor = 0
    for p in piles:
        xor ^= p

    if xor == 0:
        # Already losing? Then make a small move to prolong game
        # Find first non-zero pile and take 1
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    else:
        # Try to find a move that makes XOR = 0
        for i in range(4):
            if piles[i] == 0:
                continue
            # What would the pile be after removal?
            target = xor ^ piles[i]  # desired value after move
            take = piles[i] - target
            if 1 <= take <= piles[i]:
                return f"{i},{take}"

    # Fallback: should not happen, but pick a valid move
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
