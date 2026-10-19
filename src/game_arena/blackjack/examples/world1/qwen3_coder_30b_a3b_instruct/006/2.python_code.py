
def policy(hand: list[str], target: int) -> str:
    # Calculate the current hand value with proper Ace handling
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
        
        # Adjust for Aces - if we're over target, change Aces from 11 to 1
        while value > target and aces > 0:
            value -= 10  # Convert Ace from 11 to 1
            aces -= 1
            
        return value
    
    current_value = get_hand_value(hand)
    
    # If we're already over the target, we must STAY
    if current_value > target:
        return "STAY"
    
    # If we're at or above target, STAY
    if current_value >= target:
        return "STAY"
    
    # If we're close to target (within 4 points), be cautious
    if target - current_value <= 4:
        return "STAY"
    
    # Otherwise, HIT
    return "HIT"
