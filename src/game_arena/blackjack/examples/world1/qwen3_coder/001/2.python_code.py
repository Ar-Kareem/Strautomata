
def policy(hand: list[str], target: int) -> str:
    def calculate_hand_value(hand):
        # First calculate total without aces
        total = 0
        aces = 0
        
        for card in hand:
            if card == "A":
                aces += 1
            elif card in ["J", "Q", "K"]:
                total += 10
            else:
                total += int(card)
        
        # Add aces optimally
        for _ in range(aces):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
        
        return total
    
    current_value = calculate_hand_value(hand)
    
    # If we've already reached or exceeded target, stay
    if current_value >= target:
        return "STAY"
    
    # If we're within 2 points of target, stay to avoid risk of busting
    if target - current_value <= 2:
        return "STAY"
    
    # Otherwise, hit to try to get closer to target
    return "HIT"
