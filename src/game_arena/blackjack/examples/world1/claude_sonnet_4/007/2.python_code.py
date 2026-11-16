
def policy(hand: list[str], target: int) -> str:
    def calculate_hand_value(cards, target):
        """Calculate the optimal value of a hand given the target."""
        total = 0
        aces = 0
        
        # Count non-ace cards
        for card in cards:
            if card == "A":
                aces += 1
            elif card in ["J", "Q", "K"]:
                total += 10
            else:
                total += int(card)
        
        # Handle aces optimally - use as many 11s as possible without busting
        aces_as_eleven = 0
        for i in range(aces):
            if total + (aces_as_eleven + 1) * 11 + (aces - aces_as_eleven - 1) * 1 <= target:
                aces_as_eleven += 1
        
        total += aces_as_eleven * 11 + (aces - aces_as_eleven) * 1
        return total
    
    def get_available_cards(hand):
        """Get cards still available in the deck."""
        all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        hand_cards = hand.copy()
        available = []
        
        for card in all_cards:
            if card in hand_cards:
                hand_cards.remove(card)
            else:
                available.append(card)
        
        return available
    
    # Calculate current hand value
    current_value = calculate_hand_value(hand, target)
    
    # If we've reached the target exactly, stay
    if current_value == target:
        return "STAY"
    
    # Get available cards
    available_cards = get_available_cards(hand)
    
    # If no cards left, must stay
    if not available_cards:
        return "STAY"
    
    # Analyze outcomes of hitting
    total_cards = len(available_cards)
    bust_cards = 0
    improve_cards = 0
    
    current_distance = abs(current_value - target)
    
    for card in available_cards:
        new_hand = hand + [card]
        new_value = calculate_hand_value(new_hand, target)
        
        if new_value > target:
            bust_cards += 1
        else:
            new_distance = abs(new_value - target)
            if new_distance < current_distance:
                improve_cards += 1
    
    # Calculate probabilities
    bust_prob = bust_cards / total_cards
    improve_prob = improve_cards / total_cards
    
    # Decision logic
    # Stay if we're very close to target or bust probability is too high
    if current_distance <= 2:
        return "STAY"
    
    # Hit if improvement probability is significantly better than bust probability
    if improve_prob > bust_prob and improve_prob >= 0.25:
        return "HIT"
    
    # Conservative approach for edge cases
    if current_distance >= 6 and bust_prob < 0.3:
        return "HIT"
    
    return "STAY"
