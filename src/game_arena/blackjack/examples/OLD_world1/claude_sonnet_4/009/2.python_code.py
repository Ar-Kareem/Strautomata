
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
    
    def hand_value(hand, target):
        total = 0
        aces = 0
        
        # First pass: count non-aces and count aces
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
    
    current_value = hand_value(hand, target)
    
    # If we're already at or over target, we must stay
    if current_value >= target:
        return "STAY"
    
    # Calculate remaining cards in deck
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining_cards = []
    
    for card in all_cards:
        if card not in hand:
            remaining_cards.append(card)
    
    # If no cards left, must stay
    if not remaining_cards:
        return "STAY"
    
    # Calculate probability of busting and expected value
    bust_count = 0
    total_value_if_hit = 0
    
    for card in remaining_cards:
        new_value = current_value + card_value(card, current_value, target)
        if new_value > target:
            bust_count += 1
        else:
            total_value_if_hit += new_value
    
    non_bust_count = len(remaining_cards) - bust_count
    bust_probability = bust_count / len(remaining_cards)
    
    # Conservative strategy: if bust probability is too high, stay
    if bust_probability > 0.5:
        return "STAY"
    
    # If we're very close to target and risk is high, be more conservative
    gap_to_target = target - current_value
    
    if gap_to_target <= 3 and bust_probability > 0.3:
        return "STAY"
    
    # If we're far from target, be more aggressive
    if gap_to_target > 7:
        return "HIT"
    
    # For medium gaps, use expected value approach
    if non_bust_count > 0:
        expected_value_if_hit = total_value_if_hit / non_bust_count
        
        # Hit if expected value gets us closer to target than staying
        if abs(expected_value_if_hit - target) < abs(current_value - target):
            return "HIT"
    
    # Default to staying if uncertain
    return "STAY"
