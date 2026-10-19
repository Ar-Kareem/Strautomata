
from typing import List


def _first_legal_move(piles: List[int]) -> str:
    for i, h in enumerate(piles):
        if h > 0:
            return f"{i},1"
    # Terminal state should not be queried, but return a well-formed fallback.
    return "0,1"


def _safe_move(piles: List[int], pile: int, take: int) -> str:
    if 0 <= pile < len(piles) and 1 <= take <= piles[pile]:
        return f"{pile},{take}"
    return _first_legal_move(piles)


def policy(piles: List[int]) -> str:
    xor_sum = 0
    big_indices = []
    ones = 0

    for i, h in enumerate(piles):
        xor_sum ^= h
        if h > 1:
            big_indices.append(i)
        elif h == 1:
            ones += 1

    big_count = len(big_indices)

    # Case 1: all nonempty piles are size 1
    if big_count == 0:
        return _first_legal_move(piles)

    # Case 2: exactly one pile > 1
    if big_count == 1:
        i = big_indices[0]
        target = 1 if (ones % 2 == 0) else 0
        return _safe_move(piles, i, piles[i] - target)

    # Case 3: at least two piles > 1
    # Play normal Nim: make xor 0.
    if xor_sum != 0:
        for i, h in enumerate(piles):
            target = h ^ xor_sum
            if target < h:
                return _safe_move(piles, i, h - target)

    # Already losing under perfect play.
    # Still return a legal move; reduce the smallest big heap to 1,
    # which often leaves a trickier misère endgame for weak opponents.
    i = min(big_indices, key=lambda idx: piles[idx])
    return _safe_move(piles, i, piles[i] - 1)
