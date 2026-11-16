
def policy(hand: list[str], target: int) -> str:
    """
    Policy for simplified Blackjack-like game.
    
    Strategy:
    - Calculate current hand value
    - Estimate probability of busting on next card
    - Estimate expected value of hitting vs staying
    - Make decision based on risk/reward analysis
    """
    
    def card_value(card: str, current_sum: int, target: int) -> int:
        """Calculate the value of a card given current hand sum and target."""
        if card in ['J', 'Q', 'K']:
            return 10
        elif card == 'A':
            # Ace is 11 if it doesn't cause us to exceed target, else 1
            if current_sum + 11 <= target:
                return 11
            else:
                return 1
        else:
            return int(card)
    
    def hand_value(cards: list[str], target: int) -> int:
        """Calculate total value of hand."""
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
        
        # Adjust aces from 11 to 1 if needed
        while total > target and aces > 0:
            total -= 10
            aces -= 1
        
        return total
    
    current_value = hand_value(hand, target)
    
    # If we've busted, we should have stayed earlier (but return STAY anyway)
    if current_value > target:
        return "STAY"
    
    # If we've hit the target exactly, stay
    if current_value == target:
        return "STAY"
    
    # Determine which cards are still available in our deck
    all_cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    remaining_cards = [c for c in all_cards if c not in hand]
    
    if not remaining_cards:
        return "STAY"
    
    # Calculate expected value of hitting
    safe_cards = 0
    total_cards = len(remaining_cards)
    
    for card in remaining_cards:
        test_value = current_value + card_value(card, current_value, target)
        if test_value <= target:
            safe_cards += 1
    
    bust_probability = 1 - (safe_cards / total_cards)
    
    # Conservative strategy based on target and current value
    gap = target - current_value
    
    # If gap is very small, be more conservative
    if gap <= 3:
        return "STAY"
    
    # If gap is moderate and bust probability is low, hit
    if gap <= 6:
        if bust_probability <= 0.4:
            return "HIT"
        else:
            return "STAY"
    
    # If gap is large, be more aggressive
    if gap <= 10:
        if bust_probability <= 0.5:
            return "HIT"
        else:
            return "STAY"
    
    # If gap is very large, hit unless very risky
    if bust_probability <= 0.6:
        return "HIT"
    else:
        return "STAY"
