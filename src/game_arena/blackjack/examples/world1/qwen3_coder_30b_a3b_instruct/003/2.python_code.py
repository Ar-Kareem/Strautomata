
def policy(hand: list[str], target: int) -> str:
    # Calculate current hand value with proper Ace rules
    def hand_value(hand):
        value = 0
        aces = 0
        for card in hand:
            if card in ["J", "Q", "K"]:
                value += 10
            elif card == "A":
                aces += 1
                value += 11  # Start with 11 for A
            else:
                value += int(card)
        
        # Adjust Aces from 11 to 1 if needed to avoid busting
        while value > target and aces > 0:
            value -= 10  # Convert Ace from 11 to 1
            aces -= 1
        return value
    
    current_value = hand_value(hand)
    
    # If we're already at or over target, stay to avoid busting
    if current_value >= target:
        return "STAY"
    
    # If we're very close to target, probably safe to stay
    if current_value >= target - 5:
        return "STAY"
    
    # If we have a really weak hand, keep hitting
    if current_value <= 14:
        return "HIT"
    
    # For medium hands, use risk assessment
    # Calculate what the max possible value could be with one more card
    # Worst case after another card: total + 11 (if other is A) or 10 (if other is 10/J/Q/K)
    if current_value >= target - 10:
        # We're close to target, should be more conservative
        # But we have room for small improvements
        return "STAY"
    
    # Default behavior: if we're not too close, keep hitting
    return "HIT"
