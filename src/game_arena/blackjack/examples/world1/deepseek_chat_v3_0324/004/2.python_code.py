
def policy(hand: list[str], target: int) -> str:
    def calculate_hand_value(hand, target):
        value = 0
        aces = 0
        for card in hand:
            if card == 'A':
                aces += 1
                value += 11
            elif card in ['J', 'Q', 'K']:
                value += 10
            else:
                value += int(card)
        
        while value > target and aces > 0:
            value -= 10
            aces -= 1
        
        return value
    
    current_value = calculate_hand_value(hand, target)
    
    if current_value >= target:
        return "STAY"
    
    # Define a safe threshold (e.g., target - 3)
    safe_threshold = max(3, target - 3)
    
    if current_value >= safe_threshold:
        return "STAY"
    else:
        return "HIT"
