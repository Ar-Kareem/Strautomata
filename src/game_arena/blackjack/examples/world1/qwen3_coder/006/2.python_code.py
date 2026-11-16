
def policy(hand: list[str], target: int) -> str:
    # All possible cards in a suit
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    
    # Calculate current hand value with proper Ace handling
    def calculate_hand_value(cards):
        # First count non-Aces
        total = 0
        ace_count = 0
        
        for card in cards:
            if card == "A":
                ace_count += 1
            elif card in ["J", "Q", "K"]:
                total += 10
            else:  # 2-10
                total += int(card)
        
        # Handle Aces optimally (11 if possible, 1 if would bust)
        for _ in range(ace_count):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
                
        return total
    
    current_value = calculate_hand_value(hand)
    
    # If we've already reached or exceeded target, should probably stay
    if current_value >= target:
        return "STAY"
    
    # Find remaining cards in our deck (cards not in our hand)
    hand_set = set(hand)
    remaining_cards = [card for card in all_cards if card not in hand_set]
    
    # If no cards left, must stay
    if not remaining_cards:
        return "STAY"
    
    # Calculate possible outcomes from drawing each remaining card
    safe_draws = 0
    total_draws = len(remaining_cards)
    
    for card in remaining_cards:
        # Calculate what our new hand value would be with this card
        new_hand = hand + [card]
        new_value = calculate_hand_value(new_hand)
        
        # If we don't bust, this is a safe draw
        if new_value <= target:
            safe_draws += 1
    
    # Calculate probability of not busting
    safe_probability = safe_draws / total_draws
    
    # If we have a high probability of not busting, hit
    # If we have a low probability, stay to protect our current position
    if safe_probability > 0.5:
        return "HIT"
    else:
        return "STAY"
