
from __future__ import annotations


def _fallback_legal_move(piles: list[int]) -> str:
    """
    Return a legal move for any non-terminal state.
    If the state is terminal, no legal move exists; the arena should not call policy then.
    """
    best_i = -1
    best_h = 0

    for i, h in enumerate(piles):
        if h > best_h:
            best_h = h
            best_i = i

    if best_i >= 0 and best_h > 0:
        return f"{best_i},1"

    # Terminal position: unreachable during normal play because there is no legal move.
    return "0,0"


def _format_move(piles: list[int], pile: int, take: int) -> str:
    """Defensive formatter: ensures the returned move is legal whenever possible."""
    if 0 <= pile < len(piles) and 1 <= take <= piles[pile]:
        return f"{pile},{take}"
    return _fallback_legal_move(piles)


def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misere Nim.
    Move format: 'pile,take'
    """
    xor_sum = 0
    ones = 0
    large_indices = []

    for i, h in enumerate(piles):
        xor_sum ^= h
        if h == 1:
            ones += 1
        elif h > 1:
            large_indices.append(i)

    large_count = len(large_indices)

    # Endgame: all piles are 0 or 1.
    # With an even number of ones this is winning; with odd it is losing,
    # but the only legal move type is still to remove one singleton.
    if large_count == 0:
        return _fallback_legal_move(piles)

    # Exactly one pile larger than 1: play the misere Nim endgame rule.
    # Leave the opponent an odd number of singletons.
    if large_count == 1:
        i = large_indices[0]
        h = piles[i]

        if ones % 2 == 0:
            # Leave this large pile as a singleton, making ones + 1 odd.
            take = h - 1
        else:
            # Remove the large pile entirely, leaving an odd number of ones.
            take = h

        return _format_move(piles, i, take)

    # At least two large piles: normal Nim strategy applies.
    # If possible, move to xor 0.
    if xor_sum != 0:
        for i, h in enumerate(piles):
            target = h ^ xor_sum
            if target < h:
                take = h - target
                return _format_move(piles, i, take)

    # Losing position against perfect play: return a legal move that keeps
    # the game as nontrivial as possible.
    return _fallback_legal_move(piles)
