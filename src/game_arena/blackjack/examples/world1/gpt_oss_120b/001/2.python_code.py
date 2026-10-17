
# policy.py
from typing import List

# Fixed order of ranks in the deck
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
# Base values for non‑Ace cards
BASE_VALUES = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
    "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10
}

def best_hand_total(hand: List[str], target: int) -> int:
    """
    Returns the highest possible hand total that does not exceed `target`.
    If every possible total exceeds `target`, returns the minimal total (i.e., bust).
    """
    total = 0
    ace_count = 0
    for card in hand:
        if card == "A":
            ace_count += 1
            total += 11
        else:
            total += BASE_VALUES[card]

    # Downgrade Aces from 11 to 1 while we are over the target
    while total > target and ace_count > 0:
        total -= 10   # 11 -> 1
        ace_count -= 1
    return total

def is_bust(hand: List[str], target: int) -> bool:
    """True if the hand is inevitably over the target after optimal Ace handling."""
    return best_hand_total(hand, target) > target

def bust_probability(hand: List[str], target: int) -> float:
    """
    Computes the probability that drawing one more card from the remaining deck
    will cause a bust.
    """
    remaining = [r for r in RANKS if r not in hand]
    if not remaining:
        return 1.0  # No cards left → can't draw, treat as certain bust for safety

    busts = 0
    for card in remaining:
        new_hand = hand + [card]
        if is_bust(new_hand, target):
            busts += 1
    return busts / len(remaining)

def policy(hand: List[str], target: int) -> str:
    """
    Decide whether to HIT (draw another card) or STAY (stop drawing).

    Parameters
    ----------
    hand : list[str]
        Current cards in our hand.
    target : int
        The target score we want to approach without exceeding.

    Returns
    -------
    str
        Either "HIT" or "STAY".
    """
    # Current best total
    current_total = best_hand_total(hand, target)

    # If we have already hit the target exactly, stay.
    if current_total == target:
        return "STAY"

    # If we have no cards left to draw, we must stay.
    if len(hand) == len(RANKS):
        return "STAY"

    # Compute bust probability for the next draw
    p_bust = bust_probability(hand, target)

    # Heuristic thresholds
    SAFE_BUST_THRESHOLD = 0.20   # almost sure safe draw
    MODERATE_BUST_THRESHOLD = 0.35
    DISTANCE_FROM_TARGET = 2    # how far we are willing to be from target before staying

    # Very safe to hit
    if p_bust <= SAFE_BUST_THRESHOLD:
        return "HIT"

    # If we are still considerably below the target and the bust risk is moderate, hit
    if p_bust < MODERATE_BUST_THRESHOLD and current_total <= target - DISTANCE_FROM_TARGET:
        return "HIT"

    # Otherwise stay
    return "STAY"
