
def policy(hand: list[str], target: int) -> str:
    def calculate_hand_value(hand, target):
        """Calculate the value of a hand according to game rules."""
        total = 0
        aces = 0
        
        for card in hand:
            if card == 'A':
                aces += 1
            elif card in ['J', 'Q', 'K']:
                total += 10
            else:
                total += int(card)
        
        # Add aces: use 11 if it keeps us at or below target, otherwise use 1
        for _ in range(aces):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
        
        return total
    
    # Calculate current hand value
    current_value = calculate_hand_value(hand, target)
    
    # If we've already busted, stay (game should be over)
    if current_value > target:
        return "STAY"
    
    # Determine remaining cards in our deck
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining = [card for card in all_cards if card not in hand]
    
    # If no cards left, must stay
    if len(remaining) == 0:
        return "STAY"
    
    # Analyze what happens if we hit
    busts = 0
    safe_draws = 0
    
    for card in remaining:
        new_hand = hand + [card]
        new_value = calculate_hand_value(new_hand, target)
        
        if new_value > target:
            busts += 1
        else:
            safe_draws += 1
    
    # Calculate bust probability
    bust_prob = busts / len(remaining)
    gap = target - current_value
    
    # Decision logic based on gap to target and bust probability
    if gap <= 1:
        # Very close to target, stay
        return "STAY"
    elif gap <= 2:
        # Close to target, stay unless very safe
        if bust_prob > 0.2:
            return "STAY"
        return "HIT"
    elif gap <= 4:
        # Moderate gap, stay if risky
        if bust_prob > 0.4:
            return "STAY"
        return "HIT"
    elif gap <= 6:
        # Larger gap, more willing to risk
        if bust_prob > 0.6:
            return "STAY"
        return "HIT"
    else:
        # Far from target, hit unless very risky
        if bust_prob > 0.7:
            return "STAY"
        return "HIT"
