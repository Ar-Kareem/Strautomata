#!/usr/bin/env python3
from functools import lru_cache
from typing import List

# Ranks in a single suit deck (one of each)
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
RANK_TO_INDEX = {r: i for i, r in enumerate(RANKS)}

# Base values: A counted as 11 initially; will be adjusted if necessary
BASE_VALUE = {r: (11 if r == "A" else (10 if r in ("J", "Q", "K") else int(r))) for r in RANKS}

def policy(hand: List[str], target: int) -> str:
    """
    Decide whether to "HIT" or "STAY" given current hand and target T.
    Uses an optimal stopping DP that minimizes expected absolute distance to target,
    treating a bust as a very large penalty (strongly discouraged unless unavoidable).
    """
    # Build bitmasks for hand and remaining cards (each rank appears at most once in the deck)
    full_mask = (1 << len(RANKS)) - 1
    hand_mask = 0
    for c in hand:
        if c in RANK_TO_INDEX:
            hand_mask |= (1 << RANK_TO_INDEX[c])
    rem_mask = full_mask & (~hand_mask)

    PENALTY = 1000.0  # large penalty for busting (immediate loss)

    def hand_value_from_mask(mask: int) -> int:
        total = 0
        aces = 0
        for i, r in enumerate(RANKS):
            if (mask >> i) & 1:
                v = BASE_VALUE[r]
                total += v
                if r == "A":
                    aces += 1
        # Convert some aces from 11 to 1 (subtract 10) while total > target
        # This follows the rule: Ace = 11 when hand value <= T, else Ace = 1 when > T
        while total > target and aces > 0:
            total -= 10
            aces -= 1
        return total

    @lru_cache(maxsize=None)
    def expected_cost(hand_mask_c: int, rem_mask_c: int) -> float:
        """
        Minimal expected cost (absolute distance to target) achievable from this state
        with optimal future decisions. Bust yields PENALTY.
        """
        val = hand_value_from_mask(hand_mask_c)
        # If current hand is a bust
        if val > target:
            return PENALTY
        # Cost if we stay now
        stay_cost = abs(val - target)
        # If no remaining cards, must stay
        if rem_mask_c == 0:
            return float(stay_cost)
        # Compute expected cost if we hit once and then continue optimally
        total = 0.0
        count = 0
        m = rem_mask_c
        while m:
            lsb = m & -m
            i = (lsb.bit_length() - 1)
            m ^= lsb
            new_hand = hand_mask_c | (1 << i)
            new_rem = rem_mask_c & (~(1 << i))
            total += expected_cost(new_hand, new_rem)
            count += 1
        hit_cost = total / count if count > 0 else float('inf')
        return float(min(stay_cost, hit_cost))

    # Quick checks: if already bust or exactly at target
    current_value = hand_value_from_mask(hand_mask)
    if current_value > target:
        return "STAY"  # already busted (game over); safe default
    if current_value == target:
        return "STAY"

    # Compute stay and hit expected costs at root to choose action
    stay_cost_root = abs(current_value - target)
    # If no remaining cards, must stay
    if rem_mask == 0:
        return "STAY"

    # Expected cost of hitting (after which we'll follow optimal decisions)
    total = 0.0
    count = 0
    m = rem_mask
    while m:
        lsb = m & -m
        i = (lsb.bit_length() - 1)
        m ^= lsb
        new_hand = hand_mask | (1 << i)
        new_rem = rem_mask & (~(1 << i))
        total += expected_cost(new_hand, new_rem)
        count += 1
    hit_cost_root = total / count if count > 0 else float('inf')

    # Prefer STAY on ties (conservative)
    if hit_cost_root < stay_cost_root - 1e-9:
        return "HIT"
    else:
        return "STAY"