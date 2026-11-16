#!/usr/bin/env python3
from typing import List

# Single-file policy for simplified Blackjack-like game.
# The policy uses a lightweight one-step lookahead heuristic:
# - Compute current hand value with flexible Aces (11 or 1 as needed).
# - Compute the expected "distance" to the target if we HIT once (averaged over remaining cards in our deck).
# - Compare that to the current distance if we STAY.
# - Penalize busts heavily so we avoid unnecessary high-bust-risk hits.
#
# This is not guaranteed optimal but is a sensible, fast decision rule given only the current hand and the target.

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
VALUE_MAP = {
    "A": 11,  # initially treat Ace as 11, then reduce to 1 if needed to avoid bust
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 10,
    "Q": 10,
    "K": 10,
}

def hand_value_and_bust(cards: List[str], target: int) -> (int, bool):
    """
    Compute the best hand value <= target if possible by counting some Aces as 1.
    Return (value, bust_flag). If bust_flag is True then value is the minimal possible sum (all Aces=1).
    """
    total = 0
    aces = 0
    for c in cards:
        v = VALUE_MAP.get(c, 0)
        total += v
        if c == "A":
            aces += 1
    # Downgrade Aces from 11 to 1 (i.e., subtract 10 each time) while total > target and aces > 0
    while total > target and aces > 0:
        total -= 10
        aces -= 1
    bust = total > target
    return total, bust

def expected_distance_after_hit(hand: List[str], target: int) -> float:
    """
    Compute expected 'distance' to target after drawing exactly one card (averaged over remaining cards).
    Distance metric:
      - If not bust: absolute difference |target - value|
      - If bust: large penalty = 2 * target (encourages avoiding bust)
    """
    # Build remaining ranks in our deck (we have one of each rank; remove those in hand)
    remaining = [r for r in RANKS if r not in hand]
    if not remaining:
        # No card left to draw -> can't hit; return a very large distance
        return float("inf")
    penalties = []
    for r in remaining:
        new_hand = hand + [r]
        val, bust = hand_value_and_bust(new_hand, target)
        if bust:
            dist = 2 * target  # heavy penalty for bust
        else:
            dist = abs(target - val)
        penalties.append(dist)
    # Average over remaining cards (uniform)
    return sum(penalties) / len(penalties)

def policy(hand: List[str], target: int) -> str:
    """
    Decide whether to "HIT" (draw one more card) or "STAY" (stop drawing).
    Returns exactly "HIT" or "STAY".
    """
    # Safety: if target missing or hand malformed, stay.
    if hand is None:
        return "STAY"

    # Current value and bust status
    val, bust = hand_value_and_bust(hand, target)
    # If already busted, no point hitting
    if bust:
        return "STAY"
    # If we already hit the target exactly, stay.
    if val == target:
        return "STAY"

    # Compute current distance (if we stay)
    current_distance = abs(target - val)

    # Compute expected distance if we HIT once
    exp_hit_distance = expected_distance_after_hit(hand, target)

    # Choose action that gives smaller expected distance. Tie -> STAY (conservative).
    if exp_hit_distance + 1e-9 < current_distance:
        return "HIT"
    else:
        return "STAY"