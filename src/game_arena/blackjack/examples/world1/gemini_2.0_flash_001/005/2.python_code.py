
import random

def card_value(card: str, current_hand_value: int, target: int) -> int:
    if card.isdigit():
        return int(card)
    elif card in ("J", "Q", "K"):
        return 10
    else:  # card == "A"
        if current_hand_value + 11 <= target:
            return 11
        else:
            return 1

def calculate_hand_value(hand: list[str], target: int) -> int:
    hand_value = 0
    for card in hand:
        hand_value += card_value(card, hand_value, target)
    return hand_value

def policy(hand: list[str], target: int) -> str:
    hand_value = calculate_hand_value(hand, target)

    if hand_value > target:
        return "STAY" # Busted already according to the prompt, but we should still return STAY.

    if hand_value >= target - 5:
        return "STAY"
    else:
        return "HIT"
