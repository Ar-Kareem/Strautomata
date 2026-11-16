
def policy(hand: list[str], target: int) -> str:
    # Calculate current hand value with Aces evaluated optimally
    def hand_value(hand):
        # First, count non-Ace cards
        value = 0
        ace_count = 0
        for card in hand:
            if card == "A":
                ace_count += 1
            elif card in ["J", "Q", "K"]:
                value += 10
            else:
                value += int(card)
        
        # Add Aces optimally
        for _ in range(ace_count):
            if value + 11 <= target:
                value += 11
            else:
                value += 1
        
        return value

    current_value = hand_value(hand)
    
    # If we've already busted or reached target, stay
    if current_value >= target:
        return "STAY"
    
    # Estimate remaining cards in our deck
    all_ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining_ranks = all_ranks[:]
    
    # Remove cards already in our hand
    for card in hand:
        if card in remaining_ranks:
            remaining_ranks.remove(card)
    
    # If no cards left to draw, must stay
    if not remaining_ranks:
        return "STAY"
    
    # Calculate probability of safely drawing each remaining card
    safe_draw_prob = 0
    total_cards = len(remaining_ranks)
    
    if total_cards == 0:
        return "STAY"
    
    for card in remaining_ranks:
        # Calculate what our new value would be with this card
        test_hand = hand + [card]
        new_value = hand_value(test_hand)
        
        # If this draw keeps us under or at target, it's safe
        if new_value <= target:
            safe_draw_prob += 1
    
    # Probability of safe draw
    safe_prob = safe_draw_prob / total_cards
    
    # Calculate expected gain if we draw
    expected_gain = 0
    if safe_draw_prob > 0:
        for card in remaining_ranks:
            test_hand = hand + [card]
            new_value = hand_value(test_hand)
            if new_value <= target:
                expected_gain += (new_value - current_value)
        if safe_draw_prob > 0:
            expected_gain /= safe_draw_prob
    
    # Heuristic decision making
    distance_to_target = target - current_value
    
    # If we're very close to target, be more conservative
    if distance_to_target <= 3:
        # Stay unless we have high probability of safe improvement
        if safe_prob > 0.6 and expected_gain > 0.5:
            return "HIT"
        else:
            return "STAY"
    elif distance_to_target <= 6:
        # Moderate risk
        if safe_prob > 0.5:
            return "HIT"
        else:
            return "STAY"
    else:
        # We're far from target, be more aggressive but still cautious
        if safe_prob > 0.4:
            return "HIT"
        else:
            return "STAY"
