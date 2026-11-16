
def policy(hand: list[str], target: int) -> str:
    def card_value(card, current_sum, target):
        if card in ["J", "Q", "K"]:
            return 10
        elif card == "A":
            # Use 11 if it doesn't bust, otherwise use 1
            if current_sum + 11 <= target:
                return 11
            else:
                return 1
        else:
            return int(card)
    
    def calculate_hand_value(hand, target):
        # First pass: count aces and calculate non-ace total
        aces = hand.count("A")
        total = 0
        
        for card in hand:
            if card == "A":
                continue
            elif card in ["J", "Q", "K"]:
                total += 10
            else:
                total += int(card)
        
        # Add aces optimally
        for _ in range(aces):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
                
        return total
    
    def get_remaining_cards(hand):
        all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        remaining = []
        hand_copy = hand.copy()
        
        for card in all_cards:
            if card in hand_copy:
                hand_copy.remove(card)
            else:
                remaining.append(card)
        
        return remaining
    
    current_value = calculate_hand_value(hand, target)
    
    # If we're already at or very close to target, stay
    if current_value >= target - 1:
        return "STAY"
    
    # Get remaining cards and calculate probabilities
    remaining_cards = get_remaining_cards(hand)
    
    if not remaining_cards:
        return "STAY"
    
    # Calculate expected outcomes
    bust_count = 0
    beneficial_count = 0
    
    for card in remaining_cards:
        new_value = current_value + card_value(card, current_value, target)
        
        if new_value > target:
            bust_count += 1
        elif new_value > current_value:
            # Check if this gets us closer to target
            current_distance = target - current_value
            new_distance = target - new_value
            if new_distance < current_distance:
                beneficial_count += 1
    
    total_remaining = len(remaining_cards)
    bust_probability = bust_count / total_remaining
    beneficial_probability = beneficial_count / total_remaining
    
    # Conservative strategy: avoid busting unless very likely to benefit
    # Be more aggressive when far from target, more conservative when close
    distance_to_target = target - current_value
    
    # If we're far from target, take more risk
    if distance_to_target >= 8:
        risk_threshold = 0.6
    elif distance_to_target >= 5:
        risk_threshold = 0.4
    elif distance_to_target >= 3:
        risk_threshold = 0.3
    else:
        risk_threshold = 0.2
    
    # Hit if bust probability is acceptable and we have reasonable benefit chance
    if bust_probability <= risk_threshold and beneficial_probability > 0.3:
        return "HIT"
    
    # Also hit if we're very far from target (desperate situation)
    if distance_to_target >= 10 and bust_probability <= 0.7:
        return "HIT"
    
    return "STAY"
