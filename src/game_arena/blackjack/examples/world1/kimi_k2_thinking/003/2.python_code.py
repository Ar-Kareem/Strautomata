
def policy(hand: list[str], target: int) -> str:
    """
    Adaptive risk threshold strategy for simplified Blackjack.
    Decisions based on exact bust probability from remaining cards
    and dynamic risk tolerance scaled by distance to target.
    """
    
    def hand_value(cards):
        """Calculate optimal hand value with Ace adjustment"""
        aces = cards.count('A')
        value = sum(10 if c in ['J','Q','K'] else int(c) 
                   for c in cards if c != 'A')
        for _ in range(aces):
            value += 11 if value + 11 <= target else 1
        return value
    
    current = hand_value(hand)
    if current >= target:
        return "STAY"
    
    deck = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']
    remaining = [c for c in deck if hand.count(c) < 1]
    
    if not remaining:
        return "STAY"
    
    # Calculate exact bust probability for next draw
    bust_count = 0
    for card in remaining:
        if card == 'A':
            # Ace value depends on current hand state
            ace_val = 11 if current + 11 <= target else 1
            if current + ace_val > target:
                bust_count += 1
        elif card in ['J','Q','K']:
            if current + 10 > target:
                bust_count += 1
        else:
            if current + int(card) > target:
                bust_count += 1
    
    bust_prob = bust_count / len(remaining)
    distance = target - current
    
    # Adaptive risk thresholds: more aggressive when far from target
    if distance <= 2:
        return "HIT" if bust_prob < 0.05 else "STAY"
    if distance <= 5:
        return "HIT" if bust_prob < 0.25 else "STAY"
    if distance <= 8:
        return "HIT" if bust_prob < 0.40 else "STAY"
    
    return "HIT" if bust_prob < 0.60 else "STAY"
