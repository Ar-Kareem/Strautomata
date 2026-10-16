
def policy(hand: list[str], target: int) -> str:
    # Calculate current hand value
    value = 0
    aces = 0
    
    for card in hand:
        if card == 'A':
            aces += 1
            value += 11
        elif card in ['J', 'Q', 'K']:
            value += 10
        else:  # 2-10
            value += int(card)
    
    # Adjust for aces if needed
    while value > target and aces > 0:
        value -= 10  # convert an ace from 11 to 1
        aces -= 1
    
    # If already busted, just stay (though we've already lost)
    if value > target:
        return "STAY"
    
    # Calculate the probability that hitting will not bust us
    # We need to consider the remaining cards in our deck
    remaining_cards = {'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'} - set(hand)
    safe_cards = 0
    total_remaining = len(remaining_cards)
    
    if total_remaining == 0:
        return "STAY"
    
    for card in remaining_cards:
        new_value = value
        if card == 'A':
            new_value += 11
        elif card in ['J', 'Q', 'K']:
            new_value += 10
        else:
            new_value += int(card)
        
        # Check if we would bust with this card
        temp_aces = aces + (1 if card == 'A' else 0)
        while new_value > target and temp_aces > 0:
            new_value -= 10
            temp_aces -= 1
        
        if new_value <= target:
            safe_cards += 1
    
    probability_safe = safe_cards / total_remaining
    
    # Decide based on current value and probability
    if value < target - 5:
        # Far from target, hit unless very risky
        return "HIT" if probability_safe > 0.2 else "STAY"
    elif value < target - 2:
        # Getting closer, be more cautious
        return "HIT" if probability_safe > 0.4 else "STAY"
    elif value < target:
        # Very close, only hit if very safe
        return "HIT" if probability_safe > 0.7 else "STAY"
    else:
        # At or above target (but not busted)
        return "STAY"
