
def policy(hand: list[str], target: int) -> str:
    # Calculate current hand value
    def get_hand_value(hand):
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
        
        # Adjust aces from 11 to 1 if needed to avoid busting
        while value > target and aces > 0:
            value -= 10
            aces -= 1
            
        return value
    
    current_value = get_hand_value(hand)
    
    # If we've already busted or are at/above target, stay
    if current_value >= target:
        return "STAY"
    
    # If we're very close to target, be conservative
    if current_value >= target - 3:
        return "STAY"
    
    # If we're far from target, we want to get closer
    if current_value < target - 10:
        return "HIT"
    
    # For middle range, we're a bit more conservative but still want to progress
    # The closer we are to target, the more likely we should stay
    # If we're achieving >= 85% of the target, stay
    if current_value >= target * 0.85:
        return "STAY"
    
    # Otherwise, keep trying to get closer
    return "HIT"
