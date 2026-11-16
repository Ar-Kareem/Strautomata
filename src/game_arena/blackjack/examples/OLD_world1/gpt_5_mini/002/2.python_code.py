import math
from typing import List

# Define the full set of ranks in the single-suit deck
_RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

# Map non-Ace ranks to their fixed values
_VALUE_MAP = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10
}


def _best_total_with_aces(hand: List[str], target: int) -> int:
    """
    Compute the best total for `hand` given flexible Aces:
    - Try to use Aces as 11 as much as possible without exceeding target.
    - If impossible to be <= target, return the minimal total (all Aces as 1).
    """
    total = 0
    aces = 0
    for r in hand:
        if r == "A":
            aces += 1
        else:
            total += _VALUE_MAP[r]
    # Start by counting all Aces as 11
    total += aces * 11
    # Downgrade Aces from 11 to 1 (reduce by 10 each) until <= target or no more aces to downgrade
    while total > target and aces > 0:
        total -= 10
        aces -= 1
    return total


def policy(hand: list[str], target: int) -> str:
    """
    Decide whether to "HIT" (draw next card) or "STAY" (stop drawing).
    Strategy (heuristic):
    - Compute the best current total using flexible Aces.
    - If already busted (> target), return "STAY" (game over for the hand).
    - If exactly on target, always "STAY".
    - Evaluate the expected distance-to-target after one hit using the remaining ranks in our deck
      (we have one copy of each rank and remove ranks already in hand).
      Treat bust outcomes as a heavy penalty.
    - If the expected distance after hitting is strictly lower than current distance, "HIT", else "STAY".
    - This decision repeats on subsequent calls, allowing iterative hits.
    """
    # Safety checks
    if target <= 0:
        return "STAY"

    # Current best total
    current_total = _best_total_with_aces(hand, target)

    # If already busted or exactly at target, do not hit
    if current_total > target:
        return "STAY"
    if current_total == target:
        return "STAY"

    # Determine remaining ranks in our deck (one copy per rank)
    remaining = [r for r in _RANKS if r not in hand]
    if not remaining:
        return "STAY"

    current_distance = abs(target - current_total)

    # If even the largest possible card (11 for Ace) cannot bust us, always hit
    if current_total + 11 <= target:
        return "HIT"

    # Evaluate outcomes for each possible next card
    safe_distances = []
    bust_count = 0
    for r in remaining:
        new_hand = hand + [r]
        new_total = _best_total_with_aces(new_hand, target)
        if new_total > target:
            bust_count += 1
        else:
            safe_distances.append(abs(target - new_total))

    p_safe = (len(remaining) - bust_count) / len(remaining)

    # If no safe outcomes, hitting is guaranteed bust -> STAY
    if p_safe == 0:
        return "STAY"

    # Expected distance among safe draws
    expected_safe_distance = sum(safe_distances) / len(safe_distances) if safe_distances else float('inf')

    # Penalize busts heavily because they immediately lose (unless opponent also busts).
    # Penalty chosen relative to target to reflect severe cost of busting.
    bust_penalty = target * 2 + 10

    expected_distance_hit = p_safe * expected_safe_distance + (1 - p_safe) * bust_penalty

    # If hitting reduces expected distance to target, take the hit
    if expected_distance_hit < current_distance:
        return "HIT"

    # Otherwise stay
    return "STAY"