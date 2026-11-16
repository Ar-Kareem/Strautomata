
import itertools
from functools import lru_cache
from typing import List

# All possible ranks (our deck and opponent’s deck both have one copy of each)
ALL_CARDS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

# Numeric value used when counting all aces as 11 (the “full” total)
CARD_VALUE: dict = {
    "A": 11,
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

# Very large penalty used for a bust – it is far above any realistic distance,
# but still finite so that a tiny chance of bust does not make the whole hit
# expectation instantly infinite.
BUST_PENALTY = 10_000_000

@lru_cache(maxsize=None)
def hand_value(hand: tuple, target: int):
    """
    Returns (hand_sum, bust_flag) for the given hand and target.
    Aces are counted as 11 first; if that exceeds the target they are all
    switched to 1. The hand value is the largest total <= target.
    """
    total_non_ace = sum(CARD_VALUE[c] for c in hand if c != "A")
    aces = hand.count("A")
    total_full = total_non_ace + 11 * aces

    if total_full <= target:
        return total_full, False

    # Convert every ace to 1 and see if we are still <= target
    total_min = total_non_ace + aces   # ace counted as 1
    if total_min <= target:
        return total_min, False
    return None, True  # bust

@lru_cache(maxsize=None)
def expected_distance(hand: tuple, target: int) -> float:
    """
    Value function: minimal expected distance to the target if we play optimally
    from this hand state.
    """
    total, bust = hand_value(hand, target)
    if bust:
        return BUST_PENALTY

    stay_dist = abs(total - target)

    # Cards we could draw next (uniform random draw)
    remaining = [c for c in ALL_CARDS if c not in hand]
    if not remaining:                      # deck empty → we can only stay
        return stay_dist

    n = len(remaining)
    hit_exp = 0.0
    for c in remaining:
        prob = 1.0 / n
        next_hand = hand + (c,)
        # Sort to keep representation unique (hand order does not matter)
        next_hand_key = tuple(sorted(next_hand))
        nxt_total, nxt_bust = hand_value(next_hand_key, target)

        if nxt_bust:
            hit_exp += prob * BUST_PENALTY
        else:
            hit_exp += prob * expected_distance(next_hand_key, target)

    # Choose the better continuation (stay now or a random draw)
    return min(stay_dist, hit_exp)

def policy(hand: List[str], target: int) -> str:
    """
    Returns either "HIT" or "STAY" based on the computed expected distances.
    Always returns a legal move.
    """
    # Normalise hand for caching
    hand_key = tuple(sorted(hand))

    total, bust = hand_value(hand_key, target)
    if bust:
        # Already bust – we can only stay (no more draws)
        return "STAY"

    stay_dist = abs(total - target)

    # If there are no cards left we must stay
    remaining = [c for c in ALL_CARDS if c not in hand_key]
    if not remaining:
        return "STAY"

    n = len(remaining)
    hit_exp = 0.0
    for c in remaining:
        prob = 1.0 / n
        next_hand = hand_key + (c,)
        next_key = tuple(sorted(next_hand))
        nxt_total, nxt_bust = hand_value(next_key, target)

        if nxt_bust:
            hit_exp += prob * BUST_PENALTY
        else:
            hit_exp += prob * expected_distance(next_key, target)

    # Choose the action that gives the lower expected distance
    return "HIT" if hit_exp < stay_dist else "STAY"
