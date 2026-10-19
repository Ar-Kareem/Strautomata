
def policy(hand: list[str], target: int) -> str:
    # Define card values
    def card_value(card, current_sum):
        if card in ['J', 'Q', 'K']:
            return 10
        elif card == 'A':
            # Ace is 11 if it doesn't bust, else 1
            if current_sum + 11 <= target:
                return 11
            else:
                return 1
        else:
            return int(card)
    
    def calculate_hand_value(cards):
        # First sum non-aces
        total = 0
        aces = 0
        for c in cards:
            if c == 'A':
                aces += 1
            elif c in ['J', 'Q', 'K']:
                total += 10
            else:
                total += int(c)
        
        # Add aces - use 11 if possible, else 1
        for _ in range(aces):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
        
        return total
    
    current_value = calculate_hand_value(hand)
    
    # If already at or above target, must stay
    if current_value >= target:
        return "STAY"
    
    # Determine remaining cards in deck
    all_cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    remaining = []
    hand_copy = list(hand)
    for c in all_cards:
        if c in hand_copy:
            hand_copy.remove(c)
        else:
            remaining.append(c)
    
    if not remaining:
        return "STAY"
    
    # Calculate probability of busting if we hit
    bust_count = 0
    improve_count = 0
    total_remaining = len(remaining)
    
    for card in remaining:
        new_value = current_value + card_value(card, current_value)
        if new_value > target:
            bust_count += 1
        elif new_value > current_value:
            improve_count += 1
    
    bust_prob = bust_count / total_remaining
    
    # Calculate expected value if we hit (simplified)
    expected_if_hit = 0
    for card in remaining:
        new_value = current_value + card_value(card, current_value)
        if new_value > target:
            expected_if_hit += 0  # Bust = bad
        else:
            expected_if_hit += new_value
    expected_if_hit /= total_remaining
    
    # Strategy based on current position relative to target
    distance_to_target = target - current_value
    
    # More aggressive strategy calibration
    # If we're far from target, we should hit
    # If we're close, risk of busting matters more
    
    # Threshold based approach with dynamic risk tolerance
    # Higher targets mean we need to be more aggressive
    
    # Calculate a "safe" threshold to stay
    # This depends on remaining cards and target
    
    # Simple heuristic: stay if we're within a reasonable range and bust risk is high
    
    # Average remaining card value
    avg_card = sum(card_value(c, current_value) for c in remaining) / len(remaining)
    
    # If current value + average card would overshoot, consider staying
    if current_value + avg_card > target and current_value >= target - 4:
        if bust_prob > 0.4:
            return "STAY"
    
    # If very close to target, stay unless bust probability is very low
    if distance_to_target <= 2:
        return "STAY"
    
    if distance_to_target <= 4:
        if bust_prob > 0.35:
            return "STAY"
        return "HIT"
    
    if distance_to_target <= 6:
        if bust_prob > 0.5:
            return "STAY"
        return "HIT"
    
    # Far from target - hit unless very high bust probability
    if bust_prob > 0.65:
        return "STAY"
    
    return "HIT"
