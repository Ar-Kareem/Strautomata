
def policy(hand: list[str], target: int) -> str:
    # Helper function to calculate the value of a hand
    def calculate_hand_value(hand):
        total = 0
        aces = 0
        
        for card in hand:
            if card in ["J", "Q", "K"]:
                total += 10
            elif card == "A":
                aces += 1
                total += 11  # Start with 11
            else:  # number cards
                total += int(card)
        
        # Adjust aces from 11 to 1 if necessary
        while total > target and aces > 0:
            total -= 10  # Change one Ace from 11 to 1
            aces -= 1
            
        return total
    
    # Calculate the hand value
    hand_value = calculate_hand_value(hand)
    
    # Decision logic:
    # If we're already at or above the target, STAY
    if hand_value >= target:
        return "STAY"
    
    # If we're far from target, HIT to get closer
    if hand_value < target - 3:
        return "HIT"
    
    # In the middle zone, be a bit more conservative but still HIT if not too close
    if hand_value < target - 1:
        return "HIT"
    
    # If we're really close to target, STAY to avoid busting
    return "STAY"
