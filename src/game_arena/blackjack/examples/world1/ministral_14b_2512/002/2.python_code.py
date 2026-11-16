
import numpy as np

def calculate_hand_sum(hand: list[str], target: int) -> int:
    """Calculate the hand sum, treating aces optimally (11 if sum <= T, else 1)."""
    sum_with_ace_11 = 0
    sum_with_ace_1 = 0
    has_ace = False

    for card in hand:
        if card == "A":
            has_ace = True
            sum_with_ace_11 += 11
            sum_with_ace_1 += 1
        elif card in ["J", "Q", "K"]:
            sum_with_ace_11 += 10
            sum_with_ace_1 += 10
        else:  # "2" - "10"
            sum_with_ace_11 += int(card)
            sum_with_ace_1 += int(card)

    # If no ace, both sums are equal
    if not has_ace:
        return sum_with_ace_11

    # Choose the optimal ace count
    if sum_with_ace_11 <= target:
        return sum_with_ace_11
    else:
        return sum_with_ace_1

def policy(hand: list[str], target: int) -> str:
    """Determine whether to HIT or STAY based on the current hand and target."""
    current_sum = calculate_hand_sum(hand, target)

    # If we already have the target or more, stay
    if current_sum >= target:
        return "STAY"

    # If we're far from the target (sum <= T-10), hit
    if current_sum <= target - 10:
        return "HIT"

    # If we have an ace and are <= T-5, hit (since ace can be 1 if needed)
    if "A" in hand and current_sum <= target - 5:
        return "HIT"

    # Otherwise, stay to avoid risking a bust
    return "STAY"
