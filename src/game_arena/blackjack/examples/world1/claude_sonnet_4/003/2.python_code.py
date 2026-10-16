
def policy(hand: list[str], target: int) -> str:
    # Calculate hand value with optimal ace handling
    def hand_value(cards):
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
        
        # Convert aces from 11 to 1 if needed to avoid busting
        while total > target and aces > 0:
            total -= 10
            aces -= 1
        
        return total
    
    # Get card value for calculation
    def card_value(card):
        if card in ['J', 'Q', 'K']:
            return 10
        elif card == 'A':
            return 1  # Use 1 for calculation, will be handled in hand_value
        else:
            return int(card)
    
    # Get current hand value
    current_value = hand_value(hand)
    
    # If we've reached or exceeded target, stay
    if current_value >= target:
        return "STAY"
    
    # Determine remaining cards in deck
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining_cards = [card for card in all_cards if card not in hand]
    
    # If no cards left (shouldn't happen), stay
    if not remaining_cards:
        return "STAY"
    
    # Analyze what happens with each possible next card
    safe_cards = 0
    improve_cards = 0
    bust_cards = 0
    
    for card in remaining_cards:
        test_hand = hand + [card]
        new_value = hand_value(test_hand)
        
        if new_value > target:
            bust_cards += 1
        elif new_value <= target:
            safe_cards += 1
            if new_value > current_value:
                improve_cards += 1
    
    total_cards = len(remaining_cards)
    bust_prob = bust_cards / total_cards
    improve_prob = improve_cards / total_cards
    
    # Decision strategy based on distance from target and risk
    distance = target - current_value
    
    # If very close to target (1-2 away), be conservative
    if distance <= 2:
        return "HIT" if bust_prob <= 0.2 else "STAY"
    
    # If moderately close (3-4 away), balance risk
    elif distance <= 4:
        return "HIT" if bust_prob <= 0.4 else "STAY"
    
    # If somewhat far (5-7 away), be more aggressive
    elif distance <= 7:
        return "HIT" if bust_prob <= 0.6 else "STAY"
    
    # If very far (8+ away), be aggressive unless very risky
    else:
        return "HIT" if bust_prob <= 0.8 else "STAY"
