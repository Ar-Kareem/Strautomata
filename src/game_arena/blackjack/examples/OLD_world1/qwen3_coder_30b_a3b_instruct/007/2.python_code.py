
def policy(hand: list[str], target: int) -> str:
    # Calculate the current hand value
    def hand_value(hand):
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
        
        # Adjust aces from 11 to 1 if needed
        while value > target and aces > 0:
            value -= 10
            aces -= 1
        return value
    
    current_value = hand_value(hand)
    
    # If we've already busted, we must stay
    if current_value > target:
        return "STAY"
    
    # If we're already at or above target, stay
    if current_value >= target:
        return "STAY"
    
    # If we're close to target, be more conservative
    if current_value >= target - 3:
        # Consider the risk of busting
        # Calculate the probability of busting if we hit
        # For simplicity, we can estimate based on current value
        if current_value >= target - 1:
            return "STAY"  # Very close, be cautious
        else:
            # We're not very close, still hit
            return "HIT"
    
    # If we're far from target, we want to get closer
    # If we're really far (within 5 of target), safer to hit
    if target - current_value > 5:
        return "HIT"
    
    # If we're within 5 but not too close, evaluate carefully
    if target - current_value <= 5:
        # If hitting would likely put us over, be cautious
        # Estimate potential outcomes
        # Since we're playing with one deck, we know what cards remain
        # But for simplicity, we can estimate based on expected value
        
        # If current value is low (below 12), better to hit to get closer
        if current_value < 12:
            return "HIT"
        else:
            # If we're around mid-game, try to balance risk and reward
            # Heuristic: if we're below 16, it's usually good to hit,
            # but if we're above 16, be more conservative
            if current_value < 16:
                return "HIT"
            else:
                return "STAY"
    
    # Default action
    return "HIT"
