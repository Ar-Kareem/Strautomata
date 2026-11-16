
def policy(hand: list[str], target: int) -> str:
    """
    Policy for simplified Blackjack with variable target.
    Returns "HIT" or "STAY" based on current hand and target.
    """
    
    def hand_value(cards, target):
        """Calculate the value of a hand, handling Aces appropriately."""
        total = 0
        aces = 0
        
        for card in cards:
            if card == "A":
                aces += 1
                total += 11
            elif card in ["J", "Q", "K"]:
                total += 10
            else:
                total += int(card)
        
        # Convert Aces from 11 to 1 if total exceeds target
        while total > target and aces > 0:
            total -= 10
            aces -= 1
        
        return total
    
    # Calculate current hand value
    current_value = hand_value(hand, target)
    
    # If already over target, stay (though this shouldn't happen)
    if current_value > target:
        return "STAY"
    
    # Determine remaining cards in our deck
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining = [c for c in all_cards if c not in hand]
    
    # If no cards left, must stay
    if not remaining:
        return "STAY"
    
    # Calculate bust probability if we hit
    bust_count = 0
    for card in remaining:
        new_hand = hand + [card]
        new_value = hand_value(new_hand, target)
        if new_value > target:
            bust_count += 1
    
    prob_bust = bust_count / len(remaining)
    
    # Adaptive threshold strategy
    # Stand threshold depends on target value
    if target <= 15:
        stand_threshold = target - 2
    elif target <= 20:
        stand_threshold = target - 4
    else:
        stand_threshold = target - 5
    
    # Decision logic based on current value and bust probability
    gap_to_target = target - current_value
    
    # Far from target: hit aggressively
    if gap_to_target >= 8:
        return "HIT"
    
    # Medium distance: hit if bust probability is acceptable
    if gap_to_target >= 5:
        if prob_bust < 0.5:
            return "HIT"
        else:
            return "STAY"
    
    # Close to target: be more conservative
    if gap_to_target >= 3:
        if prob_bust < 0.35:
            return "HIT"
        else:
            return "STAY"
    
    # Very close to target: only hit if very safe
    if prob_bust < 0.25:
        return "HIT"
    
    return "STAY"
