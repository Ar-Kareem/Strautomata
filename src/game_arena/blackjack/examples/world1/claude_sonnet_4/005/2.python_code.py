
def policy(hand: list[str], target: int) -> str:
    def calculate_hand_value(cards, target_val):
        """Calculate the optimal value of a hand, handling Aces correctly."""
        total = 0
        aces = 0
        
        for card in cards:
            if card == "A":
                aces += 1
            elif card in ["J", "Q", "K"]:
                total += 10
            else:
                total += int(card)
        
        # Handle Aces - try to use as many as 11s as possible without busting
        for _ in range(aces):
            if total + 11 <= target_val:
                total += 11
            else:
                total += 1
                
        return total
    
    def get_remaining_cards(drawn_cards):
        """Get list of remaining cards in deck."""
        all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        remaining = []
        drawn_set = set(drawn_cards)
        
        for card in all_cards:
            if card not in drawn_set:
                remaining.append(card)
        
        return remaining
    
    def card_value(card):
        """Get the value of a single card (for remaining cards analysis)."""
        if card == "A":
            return 1  # We'll handle Ace logic separately
        elif card in ["J", "Q", "K"]:
            return 10
        else:
            return int(card)
    
    # Calculate current hand value
    current_value = calculate_hand_value(hand, target)
    
    # If we're already at target, stay
    if current_value == target:
        return "STAY"
    
    # If we're already over target, we've busted (shouldn't happen in valid game state)
    if current_value > target:
        return "STAY"
    
    # Get remaining cards
    remaining_cards = get_remaining_cards(hand)
    
    if not remaining_cards:
        return "STAY"
    
    # Analyze what happens if we hit
    bust_count = 0
    better_outcomes = 0
    total_outcomes = len(remaining_cards)
    expected_improvement = 0
    
    for card in remaining_cards:
        # Calculate what our hand value would be if we drew this card
        test_hand = hand + [card]
        new_value = calculate_hand_value(test_hand, target)
        
        if new_value > target:
            bust_count += 1
        else:
            # This is a safe card
            improvement = new_value - current_value
            expected_improvement += improvement
            if new_value > current_value:
                better_outcomes += 1
    
    bust_probability = bust_count / total_outcomes
    average_improvement = expected_improvement / total_outcomes if total_outcomes > 0 else 0
    
    # Decision logic
    # If bust probability is high (> 50%), be more conservative
    if bust_probability > 0.5:
        # Only hit if we're quite far from target
        if current_value < target - 5:
            return "HIT"
        else:
            return "STAY"
    
    # If bust probability is moderate (20-50%), consider current position
    elif bust_probability > 0.2:
        if current_value < target - 3:
            return "HIT"
        else:
            return "STAY"
    
    # If bust probability is low (≤ 20%), be more aggressive
    else:
        if current_value < target - 1:
            return "HIT"
        else:
            return "STAY"
