
def policy(hand: list[str], target: int) -> str:
    """
    Policy for simplified Blackjack-like game.
    Returns "HIT" to draw another card, or "STAY" to stop drawing.
    """
    
    def hand_value(cards, target):
        """Calculate the value of a hand, handling Aces optimally."""
        value = 0
        aces = 0
        
        for card in cards:
            if card == 'A':
                aces += 1
                value += 11
            elif card in ['J', 'Q', 'K']:
                value += 10
            else:
                value += int(card)
        
        # Convert Aces from 11 to 1 if needed to avoid exceeding target
        while value > target and aces > 0:
            value -= 10
            aces -= 1
        
        return value
    
    current_value = hand_value(hand, target)
    
    # If we've reached or exceeded target, STAY
    if current_value >= target:
        return "STAY"
    
    # Determine which cards remain in our deck
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining = all_cards.copy()
    for card in hand:
        remaining.remove(card)
    
    # If no cards left, STAY
    if not remaining:
        return "STAY"
    
    # Calculate how many remaining cards would cause us to bust
    bust_count = 0
    for card in remaining:
        new_hand = hand + [card]
        new_value = hand_value(new_hand, target)
        if new_value > target:
            bust_count += 1
    
    # Calculate bust probability
    bust_prob = bust_count / len(remaining)
    
    # Calculate gap to target
    gap = target - current_value
    
    # Decision logic:
    # - If gap is small (<=3), be very conservative
    # - If bust probability is high (>50%), STAY
    # - If gap is moderate and bust prob is reasonable, HIT
    
    if gap <= 3:
        return "STAY"
    
    if bust_prob > 0.5:
        return "STAY"
    
    # For larger gaps with acceptable risk, HIT
    return "HIT"
