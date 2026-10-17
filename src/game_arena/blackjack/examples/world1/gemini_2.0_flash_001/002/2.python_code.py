
import random

def policy(hand: list[str], target: int) -> str:
    """
    Implements a policy for a simplified Blackjack-like game.

    Args:
        hand: The list of strings representing the cards in hand.
        target: The target score to approach.

    Returns:
        "HIT" or "STAY" based on the policy.
    """

    def calculate_hand_value(hand: list[str]) -> int:
        """Calculates the value of a hand."""
        ace_count = 0
        total = 0
        for card in hand:
            if card.isdigit():
                total += int(card)
            elif card in ("J", "Q", "K"):
                total += 10
            elif card == "A":
                ace_count += 1

        for _ in range(ace_count):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
        return total

    hand_value = calculate_hand_value(hand)

    # Basic Strategy with target-dependent thresholds
    if hand_value <= 11:
        return "HIT"
    elif hand_value >= 17:
        return "STAY"
    else:
        # Adjust strategy based on target.
        hit_threshold = 12 + (target - 10) // 5 # Adjusted thresholds
        if hand_value < hit_threshold:
            return "HIT"
        else:
            return "STAY"
