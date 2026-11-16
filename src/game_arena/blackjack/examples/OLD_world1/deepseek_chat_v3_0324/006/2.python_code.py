
def policy(hand: list[str], target: int) -> str:
    # Calculate current hand value
    current_value = 0
    num_aces = 0
    
    for card in hand:
        if card == 'A':
            num_aces += 1
            current_value += 11
        elif card in ['J', 'Q', 'K']:
            current_value += 10
        else:
            current_value += int(card)
    
    # Adjust for aces if we're over the target
    while current_value > target and num_aces > 0:
        current_value -= 10  # Change ace from 11 to 1
        num_aces -= 1
    
    # If already busted (though policy might still be called)
    if current_value > target:
        return "STAY"
    
    # Calculate probability of busting if we hit
    remaining_cards = {'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'} - set(hand)
    bust_probability = 0.0
    cards_that_bust = 0
    total_remaining = len(remaining_cards)
    
    if total_remaining == 0:
        return "STAY"
    
    for card in remaining_cards:
        # Calculate new value if we draw this card
        if card == 'A':
            new_value = current_value + 11
        elif card in ['J', 'Q', 'K']:
            new_value = current_value + 10
        else:
            new_value = current_value + int(card)
        
        # Adjust for aces if needed
        temp_num_aces = num_aces + (1 if card == 'A' else 0)
        while new_value > target and temp_num_aces > 0:
            new_value -= 10
            temp_num_aces -= 1
        
        if new_value > target:
            cards_that_bust += 1
    
    bust_probability = cards_that_bust / total_remaining
    
    # Decide based on current value and bust probability
    if current_value >= target - 3:
        # Close to target, be conservative
        if bust_probability > 0.5:
            return "STAY"
        else:
            return "HIT" if current_value < target else "STAY"
    else:
        # Far from target, be more aggressive
        if bust_probability > 0.7:
            return "STAY"
        else:
            return "HIT"
