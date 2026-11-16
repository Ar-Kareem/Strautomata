
from typing import List

def is_P(position: List[int]) -> bool:
    """Return True if `position` is a misère Nim P‑position."""
    # case 1: all piles are 0 or 1
    all_one_or_zero = all(p <= 1 for p in position)
    if all_one_or_zero:
        # P‑positions: XOR == 1 (odd number of 1s)
        xor = position[0] ^ position[1] ^ position[2] ^ position[3]
        return xor == 1

    # case 2: at least one pile > 1
    xor = position[0] ^ position[1] ^ position[2] ^ position[3]
    return xor == 0

def policy(piles: List[int]) -> str:
    """
    Return the optimal next move for a misère Nim game with 4 piles.
    The move is a string 'i,k' where i is the 0‑based pile index and
    k (>=1) is the number of objects to take.
    """
    # No move is possible when all piles are zero – caller should not ask for it.
    if all(p == 0 for p in piles):
        raise ValueError("No legal move: all piles are empty")

    # ---- all piles are 0 or 1 (no heap larger than 1) ----
    all_one_or_zero = all(p <= 1 for p in piles)

    if all_one_or_zero:
        # XOR of the four piles
        xor = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
        # any heap with size 1 exists because we are in a playable state
        for i, p in enumerate(piles):
            if p == 1:
                return f"{i},1"
        # fallback – should never be reached
        raise ValueError("Unexpected state")

    # ---- at least one heap > 1 ----
    any_gt1 = any(p > 1 for p in piles)

    xor = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]

    # Losing (XOR == 0) – any move works; take one from a heap > 1
    if xor == 0:
        # find the first heap larger than one (or any non‑zero)
        for i, p in enumerate(piles):
            if p > 1:
                return f"{i},1"
        # (if no heap > 1, the list must be all zeros – should not happen)
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"

    # Winning (XOR != 0) – try to reach a P‑position
    # find a heap that contains the most‑significant bit of xor
    for i, p in enumerate(piles):
        if (p ^ xor) < p:
            # candidate heap i
            # Try the standard Nim reduction first
            new_size = p ^ xor
            new_piles = list(piles)
            new_piles[i] = new_size
            if is_P(new_piles):
                take = p - new_size
                return f"{i},{take}"

            # If that move would leave a non‑P position, try alternatives
            # Alternative 1: reduce the heap to exactly one object
            new_piles1 = list(piles)
            new_piles1[i] = 1
            if is_P(new_piles1):
                take1 = p - 1
                return f"{i},{take1}"

            # Alternative 2: remove the whole heap (leave it zero)
            new_piles2 = list(piles)
            new_piles2[i] = 0
            if is_P(new_piles2):
                take2 = p
                return f"{i},{take2}"

    # As a safety net, if none of the above found (should not happen),
    # pick a trivial move – remove one from any heap > 0
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
