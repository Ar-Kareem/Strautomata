
def policy(hand: list[str], target: int) -> str:
    # Calculate current hand value
    def get_hand_value(cards):
        value = 0
        num_aces = 0
        
        for card in cards:
            if card in ['J', 'Q', 'K']:
                value += 10
            elif card == 'A':
                num_aces += 1
                value += 11
            else:
                value += int(card)
        
        # Adjust aces from 11 to 1 if necessary to avoid busting
        while value > target and num_aces > 0:
            value -= 10
            num_aces -= 1
            
        return value
    
    current_value = get_hand_value(hand)
    
    # If we're already over target, we must STAY (because we'd lose immediately if we hit)
    if current_value >= target:
        return "STAY"
    
    # If we're very close to target, there's high chance of busting if we hit
    # Rule of thumb: if the safe range to reach target is small, avoid hitting
    # This is more conservative - we assume hitting when we're already within 5
    if current_value >= target - 5:
        return "STAY"
    
    # Otherwise, when we're well below target, it's usually safe to hit 
    return "HIT"
