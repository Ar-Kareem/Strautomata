
#!/usr/bin/env python3
"""
Policy for a simplified Blackjack-like game.

The function `policy(hand, target)` returns "HIT" or "STAY" based on a
deterministic, fast heuristic described in the accompanying commentary.
"""

from typing import List

# Full 13‑card deck (one copy of each rank)
FULL_DECK = [
    "A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"
]

# Fixed numeric values (Aces are handled specially)
CARD_VALUE = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
    "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10,
    "A": 11   # initially count as 11; later adjusted per target
}


def hand_value(hand: List[str], target: int) -> int:
    """
    Compute the best hand total according to the game rules:
    - Count all Aces as 11.
    - While total > target and there is at least one Ace counted as 11,
      downgrade one Ace from 11 to 1 (subtract 10).
    Returns the final total (may be > target → bust).
    """
    total = 0
    ace_as_eleven = 0
    for card in hand:
        val = CARD_VALUE[card]
        total += val
        if card == "A":
            ace_as_eleven += 1

    # Downgrade Aces while we are over the target
    while total > target and ace_as_eleven > 0:
        total -= 10          # turn one Ace from 11 to 1
        ace_as_eleven -= 1
    return total


def remaining_deck(hand: List[str]) -> List[str]:
    """
    Return a list of cards still available in our private deck.
    Each rank appears at most once; remove the cards already in `hand`.
    """
    remaining = FULL_DECK.copy()
    for card in hand:
        if card in remaining:
            remaining.remove(card)
    return remaining


def bust_probability_if_hit(hand: List[str], target: int) -> float:
    """
    Estimate the probability of busting if we draw one more card from the
    remaining deck.  The probability is exact because we enumerate all
    possible remaining cards (maximum 13).
    """
    remaining = remaining_deck(hand)
    if not remaining:   # No cards left – cannot hit
        return 1.0

    busts = 0
    for card in remaining:
        new_hand = hand + [card]
        new_total = hand_value(new_hand, target)
        if new_total > target:
            busts += 1
    return busts / len(remaining)


def policy(hand: List[str], target: int) -> str:
    """
    Decide whether to HIT or STAY.

    Heuristic:
    1. Compute current hand total (soft Ace handling).
    2. If total >= target -> STAY (cannot improve, and at target we already win).
    3. If total >= target - 1 -> STAY (very close to target).
    4. Compute bust probability for a single hit.
       - If bust probability > 0.5 -> STAY (too risky).
       - Otherwise -> HIT.
    """
    total = hand_value(hand, target)

    # Already bust or exactly at target – staying is the only sensible action
    if total > target or total == target:
        return "STAY"

    # Very close to target: prefer staying
    if total >= target - 1:
        return "STAY"

    # Estimate bust risk on the next draw
    bust_prob = bust_probability_if_hit(hand, target)

    # If the bust risk is more than 50%, stay; otherwise hit
    if bust_prob > 0.5:
        return "STAY"
    else:
        return "HIT"


# The module exposes only `policy`; everything else is internal.
__all__ = ["policy"]
