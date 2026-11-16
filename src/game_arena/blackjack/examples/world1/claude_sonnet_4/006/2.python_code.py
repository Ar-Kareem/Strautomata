
def policy(hand: list[str], target: int) -> str:
    def calculate_hand_value(cards, target):
        """Calculate optimal hand value given the target."""
        total = 0
        aces = 0
        
        # Count non-ace cards and aces
        for card in cards:
            if card == "A":
                aces += 1
            elif card in ["J", "Q", "K"]:
                total += 10
            else:
                total += int(card)
        
        # Handle aces optimally
        # Try to use as many aces as 11 as possible without exceeding target
        for _ in range(aces):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
                
        return total
    
    def get_remaining_cards(hand):
        """Get list of cards remaining in deck."""
        all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        remaining = []
        used = set(hand)
        
        for card in all_cards:
            if card not in used:
                remaining.append(card)
        
        return remaining
    
    def get_card_value(card, current_total, target):
        """Get the value a card would add to current hand."""
        if card == "A":
            # Ace is 11 if total + 11 <= target, otherwise 1
            return 11 if current_total + 11 <= target else 1
        elif card in ["J", "Q", "K"]:
            return 10
        else:
            return int(card)
    
    current_value = calculate_hand_value(hand, target)
    
    # If we're already at or very close to target, stay
    if current_value >= target:
        return "STAY"
    
    remaining_cards = get_remaining_cards(hand)
    
    if not remaining_cards:  # No cards left
        return "STAY"
    
    # Calculate bust probability and expected value
    bust_count = 0
    total_improvement = 0
    
    for card in remaining_cards:
        card_value = get_card_value(card, current_value, target)
        new_total = current_value + card_value
        
        if new_total > target:
            bust_count += 1
        else:
            # Calculate how much this improves our position
            current_distance = target - current_value
            new_distance = target - new_total
            improvement = current_distance - new_distance
            total_improvement += improvement
    
    bust_probability = bust_count / len(remaining_cards)
    
    # Conservative strategy based on current position
    distance_to_target = target - current_value
    
    # Be more aggressive when far from target, conservative when close
    if distance_to_target >= 8:
        # Far from target, accept higher risk
        risk_threshold = 0.6
    elif distance_to_target >= 5:
        # Medium distance, moderate risk
        risk_threshold = 0.4
    elif distance_to_target >= 3:
        # Close to target, low risk
        risk_threshold = 0.25
    else:
        # Very close, very conservative
        risk_threshold = 0.15
    
    # Also consider if we're likely to improve our position
    avg_improvement = total_improvement / len(remaining_cards) if remaining_cards else 0
    
    # Hit if bust probability is acceptable and we expect to improve
    if bust_probability <= risk_threshold and avg_improvement > 0:
        return "HIT"
    else:
        return "STAY"
