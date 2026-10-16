
def policy(hand: list[str], target: int) -> str:
    def card_value(card):
        if card in ["J", "Q", "K"]:
            return 10
        elif card == "A":
            return 11
        else:
            return int(card)
    
    def calculate_hand_value(hand, target):
        value = 0
        aces = 0
        
        for card in hand:
            if card == "A":
                aces += 1
                value += 11
            elif card in ["J", "Q", "K"]:
                value += 10
            else:
                value += int(card)
        
        # Convert aces from 11 to 1 if needed to avoid busting
        while value > target and aces > 0:
            value -= 10
            aces -= 1
        
        return value
    
    current_value = calculate_hand_value(hand, target)
    
    # If we're already at or above target, stay
    if current_value >= target:
        return "STAY"
    
    # Calculate remaining cards in deck
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining_cards = [card for card in all_cards if card not in hand]
    
    if not remaining_cards:
        return "STAY"
    
    # Calculate probability of busting if we hit
    bust_count = 0
    total_cards = len(remaining_cards)
    
    for card in remaining_cards:
        test_hand = hand + [card]
        test_value = calculate_hand_value(test_hand, target)
        if test_value > target:
            bust_count += 1
    
    bust_probability = bust_count / total_cards if total_cards > 0 else 1.0
    
    # Calculate expected value improvement
    improvement_sum = 0
    for card in remaining_cards:
        test_hand = hand + [card]
        test_value = calculate_hand_value(test_hand, target)
        if test_value <= target:
            # Distance to target (closer is better)
            improvement = min(0, target - test_value) - (target - current_value)
            improvement_sum += improvement
    
    expected_improvement = improvement_sum / total_cards if total_cards > 0 else 0
    
    # Decision logic based on multiple factors
    
    # If we're very close to target (within 3), be more conservative
    if target - current_value <= 3:
        if bust_probability > 0.3:
            return "STAY"
    
    # If we're far from target, be more aggressive
    if target - current_value > 7:
        if bust_probability < 0.7:
            return "HIT"
    
    # For medium distances, use a balanced approach
    # Consider both bust probability and expected improvement
    if target - current_value <= 6:
        if bust_probability > 0.4:
            return "STAY"
        else:
            return "HIT"
    
    # Default case - if we're still far and bust probability is reasonable
    if bust_probability < 0.6:
        return "HIT"
    else:
        return "STAY"
