
def policy(hand: list[str], target: int) -> str:
    # Calculate the current value of the hand
    def calculate_hand_value(hand):
        value = 0
        aces = 0
        for card in hand:
            if card in ["J", "Q", "K"]:
                value += 10
            elif card == "A":
                aces += 1
                value += 11  # Initially count A as 11
            else:
                value += int(card)
        
        # Adjust for aces if we're over the limit
        while value > target and aces > 0:
            value -= 10  # Convert an ace from 11 to 1
            aces -= 1
            
        return value
    
    current_value = calculate_hand_value(hand)
    
    # If we have already busted or reached/exceeded target, stay
    if current_value >= target:
        return "STAY"
    
    # If we're far from target, we want to draw more cards
    if current_value <= target - 10:
        return "HIT"
    
    # If we're reasonably close to target, be more cautious
    # In this case, staying might be better as we risk busting
    if current_value >= target - 5:
        return "STAY"
    
    # Otherwise (target-10 to target-5 range), take the risk of hitting
    # This heuristic aims to get near target while avoiding busting
    # But still have a reasonable chance of winning
    return "HIT"
