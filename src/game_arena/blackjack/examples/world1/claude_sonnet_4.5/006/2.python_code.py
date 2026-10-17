
def policy(hand: list[str], target: int) -> str:
    """
    Policy for simplified Blackjack-like game.
    
    Args:
        hand: List of card strings currently held
        target: Target score to approach without exceeding
    
    Returns:
        "HIT" to draw another card, "STAY" to stop drawing
    """
    
    def calculate_value(cards):
        """Calculate the value of a hand."""
        value = 0
        aces = 0
        
        for card in cards:
            if card == 'A':
                aces += 1
            elif card in ['J', 'Q', 'K']:
                value += 10
            else:
                value += int(card)
        
        # Add aces optimally (11 if it keeps us <= target, otherwise 1)
        for _ in range(aces):
            if value + 11 <= target:
                value += 11
            else:
                value += 1
        
        return value
    
    current_value = calculate_value(hand)
    
    # If we've reached or exceeded target, STAY
    if current_value >= target:
        return "STAY"
    
    # Determine which cards remain in our deck
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining_cards = [c for c in all_cards if c not in hand]
    
    # If no cards left, STAY
    if not remaining_cards:
        return "STAY"
    
    # Count how many remaining cards would NOT bust us
    safe_count = 0
    for card in remaining_cards:
        test_hand = hand + [card]
        test_value = calculate_value(test_hand)
        if test_value <= target:
            safe_count += 1
    
    # Calculate safety ratio
    safety_ratio = safe_count / len(remaining_cards)
    
    # Decision logic based on distance to target and safety
    distance_to_target = target - current_value
    
    # Very close to target: be very conservative
    if distance_to_target <= 2:
        return "STAY"
    
    # Far from target: hit if reasonable safety
    if distance_to_target >= 7:
        if safety_ratio >= 0.4:
            return "HIT"
        else:
            return "STAY"
    
    # Medium distance: use higher safety threshold
    if safety_ratio >= 0.6:
        return "HIT"
    else:
        return "STAY"
