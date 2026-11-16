
from __future__ import annotations

def _fallback_move(piles: list[int]) -> str:
    """
    Return a legal move on any non-terminal position.
    Heuristic fallback for theoretically losing positions:
    remove 1 from the largest non-empty pile.
    """
    best_i = -1
    best_p = -1
    for i, p in enumerate(piles):
        if p > best_p:
            best_p = p
            best_i = i

    if best_p > 0:
        return f"{best_i},1"

    # Terminal state should not be queried by the arena.
    # No legal move exists here, but return a syntactically valid string.
    return "0,1"


def policy(piles: list[int]) -> str:
    """
    Perfect-play policy for 4-pile misère Nim.
    Returns a legal move string: 'pile,take'
    """
    xor_sum = 0
    ones = 0
    big_indices = []

    for i, p in enumerate(piles):
        xor_sum ^= p
        if p == 1:
            ones += 1
        elif p > 1:
            big_indices.append(i)

    big_count = len(big_indices)

    # Case 1: all non-zero piles are 1
    if big_count == 0:
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
        return "0,1"  # terminal fallback

    # Case 2: exactly one pile > 1
    if big_count == 1:
        i = big_indices[0]
        p = piles[i]

        # Leave opponent an odd number of 1-heaps
        target = 1 if (ones % 2 == 0) else 0
        take = p - target

        if 1 <= take <= p:
            return f"{i},{take}"
        return _fallback_move(piles)

    # Case 3: at least two piles > 1
    # Play normal Nim: move to xor_sum == 0
    if xor_sum != 0:
        for i, p in enumerate(piles):
            target = p ^ xor_sum
            if target < p:
                take = p - target
                if 1 <= take <= p:
                    return f"{i},{take}"

    # Already in a losing position: make a safe legal move
    return _fallback_move(piles)
