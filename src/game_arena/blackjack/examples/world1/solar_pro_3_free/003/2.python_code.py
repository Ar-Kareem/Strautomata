
import random
from typing import List

# Full deck (each rank appears exactly once)
FULL_DECK = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

# Mapping from card symbol to its raw numeric value
CARD_VALUE = {
    "A": 11,
    "2": 2, "3": 3, "4": 4, "5": 5,
    "6": 6, "7": 7, "8": 8, "9": 9,
    "10": 10, "J": 10, "Q": 10, "K": 10,
}

BUST_PENALTY = 1000  # Very large distance used for bust outcomes

def _hand_total(cards: List[str], target: int) -> (int, bool):
    """Return (optimal total, bust_flag) for a given hand and target."""
    total = 0
    aces = 0
    for c in cards:
        total += CARD_VALUE[c]
        if c == "A":
            aces += 1
    # Convert excess Aces from 11 → 1 while keeping total ≤ target
    while total > target and aces > 0:
        total -= 10
        aces -= 1
    bust = total > target
    return total, bust

def _expected_distance(
    hand: List[str], target: int, seen: set
) -> float:
    """Average distance to target after drawing a random remaining card."""
    if not seen:  # No cards left
        return float("inf")
    # Compute current state
    cur_total, cur_bust = _hand_total(hand, target)
    if cur_bust:
        return BUST_PENALTY   # we are already bust, any hit is disastrous

    remaining_cards = [c for c in FULL_DECK if c not in seen]
    safe_diff_sum = 0
    bust_count = 0

    for c in remaining_cards:
        new_total, bust_flag = _hand_total(hand + [c], target)
        if bust_flag:
            safe_diff_sum += BUST_PENALTY
            bust_count += 1
        else:
            safe_diff_sum += abs(new_total - target)
        # no extra handling needed – every card has equal probability

    total_cards = len(remaining_cards)
    if total_cards == 0:
        return float("inf")

    expected_diff = safe_diff_sum / total_cards
    # If all outcomes bust, expected_diff will be huge, causing us to stay
    return expected_diff

def policy(hand: List[str], target: int) -> str:
    """
    Return the optimal move ("HIT" or "STAY") for the current state.

    The decision is based on a simple expected‑distance analysis:
    * stay if we would bust,
    * stay if there are no cards left,
    * stay if the expected distance after a random draw is larger than the
      current distance,
    * hit otherwise.  Small deterministic ties are broken by hashing the
      hand to keep behaviour reproducible.
    """
    seen = set(hand)

    # Already bust?
    cur_total, cur_bust = _hand_total(hand, target)
    if cur_bust:
        return "STAY"

    # No more cards in our deck?
    remaining = [c for c in FULL_DECK if c not in seen]
    if not remaining:
        return "STAY"

    # Expected distance after a hit
    exp_distance = _expected_distance(hand, target, seen)

    cur_distance = abs(cur_total - target)

    # Compare and decide
    if exp_distance < cur_distance - 1e-12:
        return "HIT"
    if exp_distance > cur_distance + 1e-12:
        return "STAY"

    # Very close tie – decide deterministically based on a hash of the hand
    # This prevents an opponent from learning a fixed pattern and exploiting it.
    tie_hash = hash(tuple(hand))
    return "HIT" if (tie_hash & 1) == 0 else "STAY"
