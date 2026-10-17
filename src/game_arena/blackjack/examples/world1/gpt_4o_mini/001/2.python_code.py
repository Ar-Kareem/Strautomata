
def value_of_card(card: str) -> int:
    if card.isdigit():  # For "2" to "10"
        return int(card)
    elif card in {"J", "Q", "K"}:  # Face cards
        return 10
    elif card == "A":  # Ace handling
        return 11  # We'll handle "A" value in the total calculation
    return 0

def calculate_hand_value(hand: list[str], target: int) -> int:
    total = sum(value_of_card(card) for card in hand)
    # Count Aces to adjust their value later
    ace_count = hand.count("A")
    
    # Adjust for Aces if we are over the target
    while total > target and ace_count > 0:
        total -= 10  # Count Ace as 1 instead of 11
        ace_count -= 1
    
    return total

def policy(hand: list[str], target: int) -> str:
    current_value = calculate_hand_value(hand, target)
    
    # Decision making based on current hand value and target
    if current_value < target - 5:  # Significantly below the target
        return "HIT"
    elif current_value >= target:  # Current value is at or over the target (we have busted)
        return "STAY"
    elif current_value >= target - 3:  # Close enough to the target
        return "STAY"
    else:  # In between, we might hit a bit longer if necessary
        return "HIT"
