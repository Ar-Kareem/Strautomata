
def policy(hand: list[str], target: int) -> str:
    def card_value(card: str) -> int:
        """Get base card value (Ace = 11)"""
        if card == 'A':
            return 11
        elif card in ['J', 'Q', 'K']:
            return 10
        else:
            return int(card)
    
    def calculate_hand_value(cards: list[str], target: int) -> int:
        """Calculate hand value with soft aces"""
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
        
        # Convert aces from 11 to 1 if over target
        while value > target and aces > 0:
            value -= 10
            aces -= 1
        
        return value
    
    def get_remaining_cards(hand: list[str]) -> list[str]:
        """Get cards remaining in deck"""
        all_cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        remaining = all_cards.copy()
        for card in hand:
            if card in remaining:
                remaining.remove(card)
        return remaining
    
    current_value = calculate_hand_value(hand, target)
    
    # If at or above target, must stay
    if current_value >= target:
        return "STAY"
    
    remaining = get_remaining_cards(hand)
    
    if not remaining:
        return "STAY"
    
    # Calculate outcomes for each possible draw
    safe_draws = 0
    total_new_value = 0
    
    for card in remaining:
        new_hand = hand + [card]
        new_value = calculate_hand_value(new_hand, target)
        
        if new_value <= target:
            safe_draws += 1
            total_new_value += new_value
        # busted draws don't contribute to expected value calculation
    
    n_remaining = len(remaining)
    p_safe = safe_draws / n_remaining
    
    # Expected value if we hit and don't bust
    if safe_draws > 0:
        expected_if_safe = total_new_value / safe_draws
    else:
        expected_if_safe = 0
    
    gap = target - current_value
    
    # Calculate expected final value of hitting (considering bust as losing)
    # If we bust, we get value 0 (will lose unless opponent also busts)
    # If we don't bust, we get new_value
    
    # Strategy: Compare staying vs hitting based on gap and bust probability
    # If gap is large, we're likely to lose if we stay (opponent can beat us easily)
    # If gap is small, we might be competitive staying
    
    # Estimate: what's a "winning" value?
    # Against a rational opponent, we need to be close to target
    # A rough heuristic: we need to be within ~3-4 of target to have good chances
    
    # More sophisticated: calculate expected win probability
    
    # Simple heuristic based on experimentation:
    # - If we're far from target (gap > 4), be aggressive about hitting
    # - If we're close (gap <= 3), be more conservative
    
    if gap >= 5:
        # We need to improve, hit if reasonable chance
        if p_safe >= 0.25:
            return "HIT"
    elif gap == 4:
        if p_safe >= 0.35:
            return "HIT"
    elif gap == 3:
        if p_safe >= 0.45:
            return "HIT"
    elif gap == 2:
        if p_safe >= 0.55:
            return "HIT"
    elif gap == 1:
        # Very close to target, only hit if very safe
        if p_safe >= 0.65:
            return "HIT"
    
    return "STAY"
