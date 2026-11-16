
def policy(hand: list[str], target: int) -> str:
    # Calculate the current hand value
    def calculate_hand_value(hand):
        value = 0
        aces = 0
        for card in hand:
            if card == "A":
                aces += 1
                value += 11
            elif card in ["J", "Q", "K"]:
                value += 10
            else:
                value += int(card)
        
        # Adjust for aces if needed
        while value > target and aces > 0:
            value -= 10
            aces -= 1
        
        return value
    
    current_value = calculate_hand_value(hand)
    
    # If we've already busted, we must stay
    if current_value > target:
        return "STAY"
    
    # If we're at or near the target, consider staying
    # If we're close to target, it's safer to stay
    if current_value >= target - 3:
        # Adjust the threshold based on how close we are
        if current_value >= target - 1:
            # Very close to target, be more conservative
            return "STAY"
        else:
            # Close but not too close, consider hitting to get closer
            return "HIT"
    
    # If we're far from target, we want to get closer
    # But be cautious about busting
    if current_value <= 10:
        # Very weak hand, it's good to hit
        return "HIT"
    elif current_value <= 15:
        # Moderate hand, moderate risk
        # Calculate probability of not busting with a hit
        # This logic approximates expected value
        return "HIT"
    else:
        # Strong hand, start being more careful
        # If target is high, we might still want to hit
        # But if we're comfortable, stay
        if target - current_value >= 5:
            return "HIT"
        else:
            return "STAY"
    
    # Default to HIT for safety
    return "HIT"
