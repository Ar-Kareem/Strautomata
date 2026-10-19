
from typing import List

def policy(piles: List[int]) -> str:
    """
    Return the optimal move for a misère Nim game with exactly 4 piles.
    Move format: 'pile,take' where pile is 0‑based index and take is the number
    of stones removed (1 ≤ take ≤ current size of the pile).
    """
    # If all piles are empty there is no move – this situation never occurs
    # during normal play, but we guard against it.
    if all(x == 0 for x in piles):
        # According to the arena constraints, this case should not be reachable.
        # Returning an empty string would be illegal; we raise an exception.
        raise ValueError("No legal move – all piles are zero")

    # ----------------------------------------------------------------------
    # 1. Identify whether any pile has more than one stone.
    # ----------------------------------------------------------------------
    any_big = any(x > 1 for x in piles)

    # ----------------------------------------------------------------------
    # 2. Compute Nim‑sum (xor of all pile sizes).
    # ----------------------------------------------------------------------
    xor_sum = 0
    for size in piles:
        xor_sum ^= size

    # ----------------------------------------------------------------------
    # 3. Normal Nim handling (misère Nim special case only when all piles ≤ 1).
    # ----------------------------------------------------------------------
    if any_big:
        # Normal Nim rule applies when a heap of size ≥ 2 exists.
        if xor_sum != 0:
            # Find a pile we can reduce to make the xor zero.
            for i, size in enumerate(piles):
                if size > xor_sum:
                    take = size - xor_sum   # number of stones to remove
                    # take is guaranteed to be ≥ 1 because size > xor_sum.
                    return f"{i},{take}"
        # xor_sum == 0 → current player is in a losing position.
        # Return any legal move (remove 1 from the first non‑empty pile).
        for i, size in enumerate(piles):
            if size > 0:
                return f"{i},1"
    else:
        # All piles are 0 or 1 → misère Nim parity rule.
        count_ones = sum(size == 1 for size in piles)

        # If count_ones is even we are in a winning position → flip parity.
        if count_ones % 2 == 0:
            for i, size in enumerate(piles):
                if size == 1:
                    return f"{i},1"
        else:
            # Losing position → any legal move suffices.
            for i, size in enumerate(piles):
                if size == 1:
                    return f"{i},1"

    # The logic above guarantees we never reach here for a reachable state.
    # Fallback (should not be used):
    for i, size in enumerate(piles):
        if size > 0:
            return f"{i},1"
