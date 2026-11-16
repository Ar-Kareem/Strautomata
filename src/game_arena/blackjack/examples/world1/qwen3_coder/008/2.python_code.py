
def policy(hand: list[str], target: int) -> str:
    def calculate_hand_value(cards):
        # Calculate hand value with optimal ace handling
        total = 0
        aces = 0
        
        # Count non-aces and aces
        for card in cards:
            if card == "A":
                aces += 1
            elif card in ["J", "Q", "K"]:
                total += 10
            else:
                total += int(card)
        
        # Add aces optimally (11 if doesn't bust, otherwise 1)
        for _ in range(aces):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
                
        return total
    
    current_value = calculate_hand_value(hand)
    
    # If we've already reached or exceeded target, we should stay to avoid busting
    if current_value >= target:
        return "STAY"
    
    # Calculate how much room we have
    remaining_to_target = target - current_value
    
    # If we have very little room, be conservative
    if remaining_to_target <= 3:
        return "STAY"
    
    # If we're far from target, always hit
    if remaining_to_target >= 11:
        return "HIT"
    
    # In middle ground, hit if we have reasonable chance of improving without busting
    # This is a refined threshold based on distance to target
    if remaining_to_target <= 6:
        # We're relatively close, risk of busting is higher
        return "STAY"
    else:
        # We're far enough that hitting is worth the risk
        return "HIT"
