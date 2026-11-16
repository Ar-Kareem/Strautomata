
def policy(hand: list[str], target: int) -> str:
    # Calculate the current hand value
    def get_hand_value(hand):
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
        
        # Adjust for aces if necessary
        while value > target and aces > 0:
            value -= 10
            aces -= 1
        
        return value
    
    current_value = get_hand_value(hand)
    
    # If we're already bust, we must stay (though this shouldn't happen)
    if current_value > target:
        return "STAY"
    
    # If we're at or above target, stay
    if current_value >= target:
        return "STAY"
    
    # If current value is very low, we want to take risks
    if current_value < 12:
        return "HIT"
    
    # If current value is between 12 and target-5, moderate risk
    if 12 <= current_value < target - 5:
        # If we're close to target, be more cautious
        if target - current_value <= 5:
            return "HIT" if target - current_value <= 3 else "STAY"
        else:
            return "HIT"
    
    # If close to target, play it safe
    if target - current_value <= 3:
        return "STAY"
    
    # Otherwise, play it safe
    return "STAY"
