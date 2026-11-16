
def policy(hand: list[str], target: int) -> str:
    # Calculate current hand value
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
    
    # Adjust aces from 11 to 1 if needed
    while value > target and aces > 0:
        value -= 10
        aces -= 1
    
    # If we already busted
    if value > target:
        return "STAY"  # No point in hitting
    
    # If we're already at or above target
    if value >= target:
        return "STAY"
    
    # If we're very close to target, be more conservative
    if value >= target - 3:
        # Even if we might go over, we're very close to target
        # We'll hit only if we have a very low chance of busting
        # and we believe we could get closer to target
        return "STAY" if value >= target - 2 else "HIT"
    
    # If we're at a very low value, get more aggressive
    if value <= 15:
        return "HIT"
    
    # For middle values, use a heuristic based on probability
    # The idea is that we should hit if we have a good chance of
    # getting closer to target without busting
    
    # Estimate remaining cards that won't make us bust
    # We'll simulate what cards are left (simplified)
    
    # In a real implementation, we might think about the probability
    # But for this simplified approach, we'll just use the current value
    
    # If we have a good chance of improving without busting, hit
    if value <= 16:
        return "HIT"
    elif value <= 18:
        # Be slightly more conservative
        return "HIT" if target - value > 5 else "STAY"
    else:
        # At high values, we're more likely to bust trying to get closer
        return "STAY"
    
    # Default conservative policy
    return "HIT" if value < 17 else "STAY"
