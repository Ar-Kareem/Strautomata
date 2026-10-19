
def policy(hand: list[str], target: int) -> str:
    """
    Policy for simplified Blackjack with variable target.
    """
    
    def hand_value(cards, target):
        """Calculate the value of a hand."""
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
        
        # Adjust aces from 11 to 1 if needed to avoid busting
        while total > target and aces > 0:
            total -= 10
            aces -= 1
        
        return total
    
    def card_value(card):
        """Get the value(s) a card can have."""
        if card == 'A':
            return [1, 11]  # Ace can be 1 or 11
        elif card in ['J', 'Q', 'K']:
            return [10]
        else:
            return [int(card)]
    
    # Calculate current hand value
    current_value = hand_value(hand, target)
    
    # If we've already met or exceeded target, STAY
    if current_value >= target:
        return "STAY"
    
    # Determine remaining cards in deck
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining_cards = [c for c in all_cards if c not in hand]
    
    # If no cards left, STAY
    if not remaining_cards:
        return "STAY"
    
    # Analyze what happens if we HIT
    outcomes = []
    for card in remaining_cards:
        values = card_value(card)
        for val in values:
            new_total = current_value + val
            # Check if this would be valid (ace adjustment)
            if card == 'A':
                if current_value + 11 <= target:
                    new_total = current_value + 11
                else:
                    new_total = current_value + 1
            
            outcomes.append(new_total)
    
    # Calculate statistics
    bust_count = sum(1 for v in outcomes if v > target)
    safe_count = len(outcomes) - bust_count
    
    bust_probability = bust_count / len(outcomes)
    
    # Calculate gap to target
    gap = target - current_value
    
    # Decision strategy based on gap and risk
    if gap <= 1:
        # Very close to target, don't risk it
        return "STAY"
    elif gap <= 3:
        # Close to target, only hit if very safe
        if bust_probability > 0.25:
            return "STAY"
        else:
            return "HIT"
    elif gap <= 6:
        # Medium distance, moderate risk acceptable
        if bust_probability > 0.5:
            return "STAY"
        else:
            return "HIT"
    else:
        # Far from target, accept higher risk
        if bust_probability > 0.7:
            return "STAY"
        else:
            return "HIT"
