
from typing import List

def policy(piles: List[int]) -> str:
    """
    Return a move 'pile,take' (0-based pile index, take >=1) for misère Nim (last move loses).
    Implements optimal (perfect-play) strategy for 4 piles using misère Nim theory.
    """
    # helper: check P-position under misère Nim rules
    def is_p_position(state):
        ones = sum(1 for x in state if x == 1)
        others = sum(1 for x in state if x > 1)
        if others == 0:
            # All piles are 0 or 1
            return (ones % 2) == 1
        # Otherwise use normal nim-sum
        xor = 0
        for x in state:
            xor ^= x
        return xor == 0

    # find first non-empty pile index (fallback)
    def first_nonzero(state):
        for i, x in enumerate(state):
            if x > 0:
                return i
        return 0

    # prepare stats
    ones = sum(1 for x in piles if x == 1)
    others = sum(1 for x in piles if x > 1)
    total_nonzero = sum(1 for x in piles if x > 0)

    # If all piles are 0 (shouldn't normally be called), return a legal dummy move if possible
    if total_nonzero == 0:
        return "0,1"  # illegal in real game but required to return a string; caller should not call on terminal state

    # Case: all piles are 0 or 1 -> play to leave an even number of ones for opponent
    if others == 0:
        # If number of ones is even, there is a winning move: remove 1 from any heap (leaves odd).
        # If odd, no winning move; still remove 1 (forced).
        i = first_nonzero(piles)
        return f"{i},1"

    # Case: exactly one heap > 1, special handling to aim for P-position (all heaps <=1 with odd ones)
    if others == 1:
        # Find index of the heap >1
        big_idx = next(i for i, x in enumerate(piles) if x > 1)
        big_size = piles[big_idx]
        # Count ones among the other piles
        other_ones = sum(1 for i, x in enumerate(piles) if i != big_idx and x == 1)
        # After reducing big to 0, ones will be other_ones
        # After reducing big to 1, ones will be other_ones + 1
        # We want resulting ones to be odd (P-position)
        if other_ones % 2 == 1:
            # leave big as 0
            take = big_size
        else:
            # leave big as 1
            take = big_size - 1
            if take < 1:
                take = 1  # safety, though big_size>1 ensures take>=1
        return f"{big_idx},{take}"

    # Otherwise (others >= 2): try to find a move that leads to a P-position.
    xor_sum = 0
    for x in piles:
        xor_sum ^= x

    # If current position is already a P-position, no winning move: return a safe move (remove 1 from a non-empty, prefer a >1 pile)
    if is_p_position(piles):
        # prefer removing 1 from a heap >1 to avoid immediately creating all-ones unintentionally
        for i, x in enumerate(piles):
            if x > 1:
                return f"{i},1"
        i = first_nonzero(piles)
        return f"{i},1"

    # We are in an N-position; search for a move that produces a P-position.
    # For each heap, consider candidate new sizes that can be achieved: the nim target, 1, and 0 (when legal).
    for i, p in enumerate(piles):
        if p == 0:
            continue
        candidates = []
        # candidate from normal Nim to make xor 0
        target = p ^ xor_sum
        if target < p:
            candidates.append(target)
        # candidate to reduce to 1 (useful if other piles are small)
        if p > 1:
            candidates.append(1)
        # candidate to reduce to 0 (might be useful when other piles are ones)
        candidates.append(0)
        # dedupe candidates and check legality (< p)
        seen = set()
        for new_size in candidates:
            if new_size in seen:
                continue
            seen.add(new_size)
            if not (0 <= new_size < p):
                continue
            new_state = list(piles)
            new_state[i] = new_size
            if is_p_position(new_state):
                take = p - new_size
                if take >= 1 and take <= p:
                    return f"{i},{take}"

    # As a fallback (shouldn't normally happen), remove 1 from a non-empty pile (prefer >1)
    for i, x in enumerate(piles):
        if x > 1:
            return f"{i},1"
    i = first_nonzero(piles)
    return f"{i},1"
