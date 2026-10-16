
def policy(hand: list[str], target: int) -> str:
    def calculate_hand_value(hand, target):
        value = 0
        aces = 0
        
        for card in hand:
            if card == 'A':
                aces += 1
            elif card in ['J', 'Q', 'K']:
                value += 10
            else:  # 2-10
                value += int(card)
        
        # Handle aces
        for _ in range(aces):
            if value + 11 <= target:
                value += 11
            else:
                value += 1
        
        return value
    
    current_value = calculate_hand_value(hand, target)
    
    # If we've already met or exceeded target, stay
    if current_value >= target:
        return "STAY"
    
    # Calculate remaining cards in our deck
    full_deck = {'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'}
    remaining_cards = list(full_deck - set(hand))
    
    # Calculate probabilities
    safe_cards = 0
    for card in remaining_cards:
        if card == 'A':
            # Ace could be 1 or 11 - assume worst case (11)
            new_value = current_value + 11
        elif card in ['J', 'Q', 'K']:
            new_value = current_value + 10
        else:
            new_value = current_value + int(card)
        
        if new_value <= target:
            safe_cards += 1
    
    # If we're far from target or have good odds, hit
    if current_value <= target - 10 or (safe_cards / len(remaining_cards)) > 0.5:
        return "HIT"
    else:
        return "STAY"
