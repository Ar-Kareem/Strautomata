
import random

def card_value(card: str, current_sum: int, target: int) -> int:
    """
    Calculates the value of a card in Blackjack.
    """
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
    """
    Calculates the total value of a hand in Blackjack.
    """
    total = 0
    for card in hand:
        total += card_value(card, total, target)
    return total

def policy(hand: list[str], target: int) -> str:
    """
    The Blackjack policy function.
    """
    current_sum = hand_value(hand, target)

    if current_sum > target:
        return "STAY"  # Bust prevention

    # Simple strategy: Always HIT if below a threshold. A more complex strategy may be needed for higher rewards.
    hit_threshold = target - 4 # Hit more often when far from target. Experiment with this value.


    if current_sum <= hit_threshold:
        return "HIT"
    else:
        return "STAY"
