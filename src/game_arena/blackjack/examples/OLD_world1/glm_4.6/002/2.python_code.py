
"""
Policy for a simplified Blackjack‑like game.

The function `policy(hand, target)` returns either "HIT" or "STAY".
It estimates the probability of busting on the next draw and compares
that to a risk tolerance that shrinks as the current hand value gets
closer to the target.
"""

from typing import List

# All ranks in a single suit
ALL_RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

# Numeric value of each rank (Ace counted as 11 initially)
CARD_VALUE = {
    'A': 11,
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10,
}


def hand_value(hand: List[str], target: int) -> int:
    """
    Compute the best possible total for the given hand respecting the target.
    Aces count as 11 unless that would exceed the target, in which case they
    count as 1. Multiple aces are converted one by one as needed.
    """
    total = 0
    aces = 0
    for card in hand:
        if card == 'A':
            aces += 1
            total += 11
        else:
            total += CARD_VALUE[card]

    # Convert aces from 11 to 1 while the total exceeds the target.
    while total > target and aces > 0:
        total -= 10
        aces -= 1
    return total


def policy(hand: List[str], target: int) -> str:
    """
    Decide whether to HIT or STAY.

    The strategy:
      * Compute the current hand value (optimal Ace usage).
      * If we have already reached or exceeded the target, we stay.
      * Determine which cards remain in our deck.
      * Estimate the probability that the next card would bust us.
      * Accept a risk that is proportional to how far we are from the target.
        The farther we are, the more bust risk we tolerate.
      * Hit if the bust probability is within the tolerated risk; otherwise stay.
    """
    current_val = hand_value(hand, target)

    # Already at or above target → no reason to hit.
    if current_val >= target:
        return "STAY"

    # Cards still available in our personal deck.
    remaining = [c for c in ALL_RANKS if c not in hand]
    if not remaining:                     # Deck exhausted.
        return "STAY"

    # Count cards that would cause an immediate bust.
    bust_count = 0
    for card in remaining:
        new_val = hand_value(hand + [card], target)
        if new_val > target:
            bust_count += 1

    bust_prob = bust_count / len(remaining)

    # Risk tolerance: the closer to the target, the less risk we accept.
    # Normalised to [0, 1] with a minimal floor of 0.1 to avoid overly
    # aggressive play when the target is very low.
    risk_tolerance = max(0.1, (target - current_val) / target)

    return "HIT" if bust_prob <= risk_tolerance else "STAY"


__all__ = ["policy"]
