
from typing import List

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
VALUE_MAP = {
    "A": 11,  # starting point for A; will be adjusted
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


def hand_value(cards: List[str], target: int) -> int:
    """
    Compute best hand value with Aces counted as 11 when possible (but reduced to 1 as needed)
    so the resulting sum is the largest sum <= target if possible, otherwise the minimal sum.
    """
    total = 0
    aces = 0
    for c in cards:
        if c == "A":
            aces += 1
            total += 11
        else:
            total += VALUE_MAP.get(c, 0)
    # Reduce Aces from 11 to 1 (subtract 10) while sum > target and there are aces counted as 11
    while total > target and aces > 0:
        total -= 10
        aces -= 1
    return total


def expected_distance_after_one_hit(hand: List[str], target: int) -> float:
    """
    Compute expected 'distance' to target after taking exactly one more card and then staying.
    Distance is defined as:
      - if bust (sum > target): large penalty
      - else: (target - sum) (smaller is better)
    This is a simple proxy for win-likelihood when opponent is unknown.
    """
    # Remaining ranks in our deck (one copy of each rank total)
    remaining = [r for r in RANKS if r not in hand]
    if not remaining:
        # no cards left to draw; hitting is impossible / same as staying
        current = hand_value(hand, target)
        if current > target:
            return target + 100.0
        return float(target - current)

    penalty_for_bust = target + 50.0  # large penalty for busting
    total = 0.0
    for r in remaining:
        new_hand = hand + [r]
        v = hand_value(new_hand, target)
        if v > target:
            total += penalty_for_bust
        else:
            total += (target - v)
    return total / len(remaining)


def policy(hand: List[str], target: int) -> str:
    """
    Simple one-step lookahead policy:
    - Compute current hand value (best Ace handling).
    - If current equals target -> STAY.
    - If current already bust ( > target) -> STAY (game over).
    - Compare current distance (target - value) vs expected distance after one HIT
      (where we assume we will STAY after that draw). Choose action with lower expected distance.
    """
    # Defensive copy
    hand = list(hand)

    current_value = hand_value(hand, target)

    # If we already hit target, stay.
    if current_value == target:
        return "STAY"
    # If already busted, staying (game already decided)
    if current_value > target:
        return "STAY"

    current_distance = float(target - current_value)
    after_hit_distance = expected_distance_after_one_hit(hand, target)

    # If hitting yields strictly better (smaller) expected distance, hit; otherwise stay.
    if after_hit_distance + 1e-9 < current_distance:
        return "HIT"
    # Conservative tie-break: prefer STAY when equal expected distances
    return "STAY"
