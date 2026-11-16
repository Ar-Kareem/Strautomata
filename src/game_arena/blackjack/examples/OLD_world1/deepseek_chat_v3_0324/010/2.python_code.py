
def calculate_hand_value(hand: list[str], target: int) -> int:
    """Calculate the value of the current hand."""
    value = 0
    aces = 0
    
    for card in hand:
        if card == 'A':
            value += 11
            aces += 1
        elif card in ['J', 'Q', 'K']:
            value += 10
        else:
            value += int(card)
    
    # Adjust for aces if needed
    while value > target and aces > 0:
        value -= 10
        aces -= 1
    
    return value

def policy(hand: list[str], target: int) -> str:
    current_value = calculate_hand_value(hand, target)
    
    # Immediate win condition if we're exactly at target
    if current_value == target:
        return "STAY"
    
    # If we've already busted (shouldn't happen as the game would end)
    if current_value > target:
        return "STAY"
    
    # If we're close to the target, stay
    if current_value >= target - 3:
        return "STAY"
    
    # Calculate the "safe" threshold based on target
    if target <= 15:
        hit_threshold = target - 4
    elif target <= 20:
        hit_threshold = target - 5
    elif target <= 25:
        hit_threshold = target - 6
    else:
        hit_threshold = target - 7
    
    # If we're below the hit threshold, hit
    if current_value <= hit_threshold:
        return "HIT"
    
    # For high targets and medium hands, sometimes we need to be more aggressive
    # to avoid being too far from target
    if target >= 20 and current_value < target - 2 and len(hand) < 3:
        return "HIT"
    
    # Conservative approach for remaining cases
    return "STAY"
