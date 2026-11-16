
from typing import List

def policy(piles: List[int]) -> str:
    """Return an optimal move for a misère Nim position with four piles.

    The returned string has the form 'pile,take' where ``pile`` is a 0‑based index
    and ``take`` is the number of objects removed from that pile.
    """
    # Helper: count how many piles are non‑zero
    def count_nonzero(arr: List[int]) -> int:
        return sum(1 for x in arr if x > 0)

    # Compute xor of all pile sizes
    total_xor = 0
    for x in piles:
        total_xor ^= x

    # ------------------------------------------------------------------
    # Case 1: every non‑empty pile is size 1
    if all(p == 1 for p in piles):
        # Remove one whole pile (any non‑zero pile works)
        for i, x in enumerate(piles):
            if x > 0:
                return f"{i},{x}"  # x is 1
    # ------------------------------------------------------------------
    # From here on at least one pile > 1 exists
    # If xor is already zero we are in a losing position; any move loses.
    if total_xor == 0:
        # Lose by taking 1 from the first non‑empty pile
        for i, x in enumerate(piles):
            if x > 0:
                return f"{i},1"
    # ------------------------------------------------------------------
    # total_xor != 0 : try the normal Nim move (make xor zero)
    for i, x in enumerate(piles):
        new_x = x ^ total_xor
        if new_x < x:  # legal reduction
            take = x - new_x
            new_piles = piles.copy()
            new_piles[i] = new_x

            # Is the resulting position a P‑position?
            # It is a P‑position if either:
            #   * xor is zero and there is at least one pile >1 (handled by "not all ones")
            #   * all piles are size 1 and the number of non‑zero piles is odd.
            if all(p == 0 or p == 1 for p in new_piles):
                # All non‑zero piles are 1 – check parity
                cnt = count_nonzero(new_piles)
                if cnt % 2 == 1:  # odd -> P‑position
                    return f"{i},{take}"
                # else even -> not a P‑position, keep searching
            else:
                # Not all ones, xor is zero, and a pile >1 exists – P‑position
                return f"{i},{take}"
    # ------------------------------------------------------------------
    # If we reach here, the xor‑zero move always left all ones with even count.
    # Try an alternative: reduce a larger pile to 1 (if it makes the count odd).
    for i, x in enumerate(piles):
        if x > 1:
            new_piles = piles.copy()
            new_piles[i] = 1
            if count_nonzero(new_piles) % 2 == 1:
                return f"{i},{x - 1}"
    # As a last resort, remove a whole pile >1 (if it yields odd count).
    for i, x in enumerate(piles):
        if x > 1:
            new_piles = piles.copy()
            new_piles[i] = 0
            if count_nonzero(new_piles) % 2 == 1:
                return f"{i},{x}"
    # ------------------------------------------------------------------
    # Fallback – should never be needed, but ensures a legal move is returned.
    for i, x in enumerate(piles):
        if x > 0:
            return f"{i},1"
    # No non‑zero piles – the game is already over.
    raise RuntimeError("No legal move available (empty position).")
