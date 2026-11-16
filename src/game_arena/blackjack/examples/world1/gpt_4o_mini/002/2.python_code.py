
def card_value(card: str) -> int:
    if card in ["J", "Q", "K"]:
        return 10
    elif card == "A":
        return 11  # Initially treat Ace as 11
    else:
        return int(card)

def hand_value(hand: list[str], target: int) -> int:
    total = 0
    aces = 0
    for card in hand:
        total += card_value(card)
        if card == "A":
            aces += 1
    
    # Adjust for Aces if necessary
    while total > target and aces > 0:
        total -= 10  # Consider Ace as 1 instead of 11
        aces -= 1
    
    return total

def policy(hand: list[str], target: int) -> str:
    current_value = hand_value(hand, target)
    
    # Define thresholds for strategy
    if current_value < target - 3:  # If less than target - 3, it's safe to HIT
        return "HIT"
    else:  # Otherwise, we STAY
        return "STAY"
