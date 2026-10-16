
def policy(hand: list[str], target: int) -> str:
    """
    Policy for simplified Blackjack-like game.
    
    Strategy:
    - Calculate current hand value
    - Estimate probability of busting on next card
    - Estimate expected value of hitting vs staying
    - Make decision based on risk/reward analysis
    """
    
    def card_value(card: str, current_sum: int, target: int) -> int:
        """Calculate the value of a single card given current hand state."""
        if card in ['J', 'Q', 'K']:
            return 10
        elif card == 'A':
            # Ace is 11 if it doesn't bust us, otherwise 1
            return 11 if current_sum + 11 <= target else 1
        else:
            return int(card)
    
    def hand_value(cards: list[str], target: int) -> int:
        """Calculate total value of hand with optimal Ace handling."""
        total = 0
        aces = 0
        
        for card in cards:
            if card == 'A':
                aces += 1
                total += 11
            elif card in ['J', 'Q', 'K']:
                total += 10
            else:
                total += int(card)
        
        # Convert Aces from 11 to 1 if we're over target
        while total > target and aces > 0:
            total -= 10
            aces -= 1
        
        return total
    
    # Get current hand value
    current_value = hand_value(hand, target)
    
    # If we've already busted, we have no choice (shouldn't happen in valid game)
    if current_value > target:
        return "STAY"
    
    # Determine which cards are still available in our deck
    all_cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    remaining_cards = [card for card in all_cards if card not in hand]
    
    if not remaining_cards:
        return "STAY"
    
    # Calculate expected outcome of hitting
    bust_count = 0
    expected_value_sum = 0
    
    for card in remaining_cards:
        # Calculate what our hand value would be with this card
        test_hand = hand + [card]
        new_value = hand_value(test_hand, target)
        
        if new_value > target:
            bust_count += 1
            expected_value_sum += 0  # Busting gives us 0 expected value
        else:
            expected_value_sum += new_value
    
    num_remaining = len(remaining_cards)
    bust_probability = bust_count / num_remaining
    avg_value_if_hit = expected_value_sum / num_remaining
    
    # Decision logic based on multiple factors
    
    # If we're at or very close to target, stay
    if current_value >= target:
        return "STAY"
    
    # If we're very far from target and bust probability is low, hit
    if current_value <= target - 10 and bust_probability < 0.3:
        return "HIT"
    
    # Dynamic threshold based on target and current position
    # The closer we are to target, the more conservative we become
    distance_to_target = target - current_value
    
    # Calculate a risk-adjusted threshold
    # Higher target means we can afford to be more aggressive early on
    if target >= 25:
        # High target: be more aggressive
        safe_threshold = min(target - 5, 20)
    elif target >= 20:
        # Medium target: moderate approach
        safe_threshold = min(target - 4, 17)
    elif target >= 15:
        # Lower target: be conservative
        safe_threshold = min(target - 3, 13)
    else:
        # Very low target: very conservative
        safe_threshold = min(target - 2, 10)
    
    # If we're below the safe threshold, hit
    if current_value < safe_threshold:
        return "HIT"
    
    # For borderline cases, use probability analysis
    # Expected value of staying is just our current value
    # Expected value of hitting needs to account for bust risk
    
    # Estimate opponent's likely score (roughly target - 2 to target)
    # If we stay, we need to beat the opponent
    # Simple heuristic: opponent will likely get close to target
    estimated_opponent_score = target - 2
    
    # If our current score is likely to lose and bust risk is acceptable, hit
    if current_value < estimated_opponent_score and bust_probability < 0.5:
        return "HIT"
    
    # If bust probability is high, stay
    if bust_probability > 0.5:
        return "STAY"
    
    # Default: if we're reasonably close to target, stay
    if distance_to_target <= 4:
        return "STAY"
    
    # Otherwise hit
    return "HIT"
