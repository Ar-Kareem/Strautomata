
import random

def card_value(card: str, current_sum: int, target: int) -> int:
    """Calculates the value of a card in Blackjack."""
    if card.isdigit():
        return int(card)
    elif card in ("J", "Q", "K"):
        return 10
    else:  # card == "A"
        if current_sum + 11 <= target:
            return 11
        else:
            return 1


def hand_value(hand: list[str], target: int) -> int:
    """Calculates the total value of a hand."""
    total = 0
    for card in hand:
        total += card_value(card, total, target)
    return total


def policy(hand: list[str], target: int) -> str:
    """
    Implements a policy for a simplified Blackjack-like game.

    Args:
        hand: A list of strings representing the cards you currently hold.
        target: The target score T you are trying to approach.

    Returns:
        "HIT" if you should draw another card, "STAY" if you should stop.
    """
    current_sum = hand_value(hand, target)

    if current_sum > target:
        return "STAY"  # Already busted, no point in hitting

    # Simple strategy: Hit if below a certain threshold, stay otherwise.
    # Adjust the threshold based on the target value to be more aggressive
    # when the target is high and more conservative when it's low.
    threshold = target - 4 # Reduce this value for more aggressive hitting

    if current_sum < threshold:
        return "HIT"
    else:
        return "STAY"
