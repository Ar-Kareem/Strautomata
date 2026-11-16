
import random

def card_value(card: str, current_hand_value: int, target: int) -> int:
    """
    Converts a card string to its integer value, handling "A" specially.
    """
    if card.isdigit():
        return int(card)
    elif card in ("J", "Q", "K"):
        return 10
    else:  # card == "A"
        if current_hand_value + 11 <= target:
            return 11
        else:
            return 1

def hand_value(hand: list[str], target: int) -> int:
    """
    Calculates the total value of a hand, considering Aces.
    """
    total = 0
    aces = 0
    for card in hand:
        if card == "A":
            aces += 1
        else:
            total += card_value(card, total, target)

    for _ in range(aces):
        if total + 11 <= target:
            total += 11
        else:
            total += 1

    return total

def policy(hand: list[str], target: int) -> str:
    """
    Determines whether to "HIT" or "STAY" based on the current hand and target.
    """
    hand_total = hand_value(hand, target)

    if hand_total > target:
        return "STAY"
    elif hand_total >= 17:  # Threshold for staying
        return "STAY"
    else:
        return "HIT"
