
def policy(hand: list[str], target: int) -> str:
    # Calculate hand value with proper Ace handling
    def get_hand_value(hand):
        value = 0
        aces = 0
        for card in hand:
            if card in ["J", "Q", "K"]:
                value += 10
            elif card == "A":
                aces += 1
                value += 11  # Initially count Aces as 11
            else:
                value += int(card)
        
        # Adjust for Aces if necessary
        # If value > target, try to reduce Aces from 11 to 1
        while value > target and aces > 0:
            value -= 10  # Convert one Ace from 11 to 1
            aces -= 1
            
        return value

    current_value = get_hand_value(hand)
    
    # If we already have a value that's at or above target,
    # we should STAY (can't improve or risk busting)  
    if current_value >= target:
        return "STAY"
    
    # If we're quite far from target, take a risk and HIT
    if current_value <= target - 10:
        return "HIT"
    
    # If we're in the middle range, we should be somewhat conservative
    # A good heuristic: if we're around 17-20 and close to target, STAY
    if current_value >= 17 and current_value < target:
        return "STAY"
    
    # Otherwise, since we're not too far behind, we might want to try getting closer
    # But we shouldn't be too aggressive in the middle region
    # Just hit if we have a good margin to improve
    if current_value < 17:
        return "HIT"
    else:
        # For values near 17-20 and far from target, be conservative
        return "STAY"
