
def policy(hand: list[str], target: int) -> str:
    def calculate_hand_value(hand, target):
        """Calculate the best hand value, handling Aces appropriately."""
        total = 0
        aces = 0
        
        for card in hand:
            if card == "A":
                aces += 1
                total += 11  # Start by counting Ace as 11
            elif card in ["J", "Q", "K"]:
                total += 10
            else:
                total += int(card)
        
        # Convert Aces from 11 to 1 if necessary to avoid busting
        while total > target and aces > 0:
            total -= 10  # Convert an Ace from 11 to 1
            aces -= 1
            
        return total
    
    def get_remaining_cards(hand):
        """Get list of cards still available in deck."""
        all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        remaining = all_cards.copy()
        
        for card in hand:
            remaining.remove(card)
            
        return remaining
    
    def get_card_value(card, current_total, target):
        """Get the value a card would add to current hand."""
        if card == "A":
            # Use 11 if it doesn't bust, otherwise 1
            return 11 if current_total + 11 <= target else 1
        elif card in ["J", "Q", "K"]:
            return 10
        else:
            return int(card)
    
    # Calculate current hand value
    current_value = calculate_hand_value(hand, target)
    
    # If we're already at or very close to target, stay
    if current_value >= target:
        return "STAY"
    
    # Get remaining cards and calculate bust probability
    remaining_cards = get_remaining_cards(hand)
    
    if not remaining_cards:  # No cards left
        return "STAY"
    
    # Calculate how many remaining cards would cause us to bust
    bust_cards = 0
    safe_cards = 0
    good_cards = 0  # Cards that get us close to target
    
    for card in remaining_cards:
        card_value = get_card_value(card, current_value, target)
        new_total = current_value + card_value
        
        if new_total > target:
            bust_cards += 1
        else:
            safe_cards += 1
            # Consider cards that get us to within 2 of target as "good"
            if new_total >= target - 2:
                good_cards += 1
    
    bust_probability = bust_cards / len(remaining_cards)
    good_probability = good_cards / len(remaining_cards)
    
    # Decision logic based on current position and probabilities
    distance_to_target = target - current_value
    
    # If we're far from target and bust probability is low, hit
    if distance_to_target >= 6 and bust_probability <= 0.5:
        return "HIT"
    
    # If we're moderately far and bust probability is very low, hit
    if distance_to_target >= 4 and bust_probability <= 0.3:
        return "HIT"
    
    # If we're close but there's a good chance of improvement with low bust risk, hit
    if distance_to_target >= 2 and bust_probability <= 0.2 and good_probability >= 0.3:
        return "HIT"
    
    # If we're very close to target, stay unless bust probability is very low
    if distance_to_target <= 1:
        return "STAY"
    
    # For edge cases, be conservative if bust probability is high
    if bust_probability >= 0.5:
        return "STAY"
    
    # Default to hitting if we're not close enough
    if distance_to_target >= 3:
        return "HIT"
    
    return "STAY"
