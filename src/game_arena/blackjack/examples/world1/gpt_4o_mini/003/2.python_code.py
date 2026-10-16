
import random

def card_value(card: str) -> int:
    if card == "A":
        return 0  # Special case for A handled in the main logic
    elif card in ("J", "Q", "K"):
        return 10
    else:
        return int(card)

def hand_value(hand: list[str], target: int) -> int:
    total = 0
    ace_count = 0
    
    for card in hand:
        if card == "A":
            ace_count += 1
        else:
            total += card_value(card)
    
    # For aces: initially consider them as 11, but adjust if necessary
    total += ace_count * 11
    
    while total > target and ace_count > 0:
        total -= 10  # Change an Ace's value from 11 to 1
        ace_count -= 1

    return total

def policy(hand: list[str], target: int) -> str:
    current_value = hand_value(hand, target)

    if current_value > target:
        return "STAY"  # This is unnecessary as you should already be bust here if you reached "policy".

    # Decision making: aggressively hit if far from target, cautious if near.
    threshold_distance = 3  # How far we can be from target to still hit
    
    # If we are below the target by more than 3, we should continue hitting
    if target - current_value > threshold_distance:
        return "HIT"

    # If we are close to target, we might want to stay
    return "STAY" 

# Example usage:
# The function can be tested with various hands and targets.
# target = random.randint(10, 30)
# hand = ["A", "9"]
# print(policy(hand, target))
