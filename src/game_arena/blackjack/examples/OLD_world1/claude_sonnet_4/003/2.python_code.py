
def policy(hand: list[str], target: int) -> str:
    def card_value(card: str, current_sum: int, target: int) -> int:
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
    
    def calculate_hand_value(hand: list[str], target: int) -> int:
        total = 0
        aces = 0
        
        # First pass: count non-ace cards and count aces
        for card in hand:
            if card == "A":
                aces += 1
            elif card in ["J", "Q", "K"]:
                total += 10
            else:
                total += int(card)
        
        # Second pass: add aces optimally
        for _ in range(aces):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
        
        return total
    
    current_value = calculate_hand_value(hand, target)
    
    # If we're already at or over target, stay
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
        new_value = current_value + card_value(card, current_value, target)
        if new_value > target:
            bust_count += 1
    
    bust_probability = bust_count / total_cards if total_cards > 0 else 1.0
    
    # Calculate expected value of hitting vs staying
    # If we're far from target and bust probability is low, hit
    distance_to_target = target - current_value
    
    # Dynamic strategy based on target and current position
    if distance_to_target >= 7:
        # We're far from target, be more aggressive
        hit_threshold = 0.6
    elif distance_to_target >= 4:
        # Medium distance, moderate risk
        hit_threshold = 0.4
    else:
        # Close to target, be conservative
        hit_threshold = 0.25
    
    # Also consider if we have a very low score relative to target
    if current_value < target * 0.6:
        hit_threshold = 0.7
    
    if bust_probability <= hit_threshold:
        return "HIT"
    else:
        return "STAY"
