
def policy(hand: list[str], target: int) -> str:
    # Calculate the current hand value
    def hand_value(hand):
        value = 0
        aces = 0
        for card in hand:
            if card in ["J", "Q", "K"]:
                value += 10
            elif card == "A":
                aces += 1
                value += 11
            else:
                value += int(card)
        
        # Adjust aces from 11 to 1 if necessary
        while value > target and aces > 0:
            value -= 10
            aces -= 1
        
        return value
    
    current_value = hand_value(hand)
    
    # If we've already busted, stay (though this shouldn't happen in normal gameplay)
    if current_value > target:
        return "STAY"
    
    # If we're at or above target, stay
    if current_value >= target:
        return "STAY"
    
    # If we're close to target, be cautious
    if current_value >= target - 3:
        # If we're within 3 of target, we might want to stay to avoid busting
        # But we still need to consider the risk
        if current_value >= target - 1:
            # Very close to target, stay
            return "STAY"
        else:
            # Close but not too close, risk a hit
            return "HIT"
    
    # If we're significantly below target, hit
    if current_value < target - 10:
        return "HIT"
    
    # In the middle range, make decision based on probability
    # If we're at a low value (like 6 or lower), hit
    if current_value <= 11:
        return "HIT"
    
    # If we're in a moderate range, be more cautious
    if current_value <= 16:
        # If we're in the middle, consider the target
        # If we're less than target - 5, hit; otherwise stay
        if current_value < target - 5:
            return "HIT"
        else:
            return "STAY"
    
    # If we're above 16 and below target, stay
    return "STAY"
