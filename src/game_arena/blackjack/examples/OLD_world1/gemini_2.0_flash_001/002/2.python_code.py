
import random

def card_value(card: str, current_sum: int, target: int) -> int:
    """
    Returns the integer value of a card.
    """
    if card.isdigit():
        return int(card)
    elif card in ("J", "Q", "K"):
        return 10
    else:  # card == "A"
        if current_sum <= target - 11:
            return 11
        else:
            return 1


def hand_value(hand: list[str], target: int) -> int:
    """
    Calculates the total value of a hand.
    """
    total = 0
    for card in hand:
        total += card_value(card, total, target)
    return total


def policy(hand: list[str], target: int) -> str:
    """
    Implements a policy for a simplified Blackjack-like game.
    """
    current_sum = hand_value(hand, target)

    if current_sum > target:
        return "STAY"  # Technically, we are busted, but we need to return STAY to end game
    
    if current_sum >= target - 2 :
      return "STAY"

    if current_sum >= 17:
        return "STAY"
    
    if current_sum <= 11:
        return "HIT"
        
    #Otherwise make a random choice
    if random.random() < 0.6:
      return "HIT"
    else:
      return "STAY"
