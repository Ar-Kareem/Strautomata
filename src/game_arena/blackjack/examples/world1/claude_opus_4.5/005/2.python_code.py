
def policy(hand: list[str], target: int) -> str:
    def card_value(card):
        if card in ['J', 'Q', 'K']:
            return 10
        elif card == 'A':
            return 11
        else:
            return int(card)
    
    def hand_value(cards, T):
        total = 0
        aces = 0
        for card in cards:
            if card == 'A':
                aces += 1
                total += 11
            else:
                total += card_value(card)
        
        # Convert aces from 11 to 1 as needed to stay at or below T
        while total > T and aces > 0:
            total -= 10
            aces -= 1
        
        return total
    
    current = hand_value(hand, target)
    
    # If we're at or above target, definitely stay
    if current >= target:
        return "STAY"
    
    # Calculate remaining cards in our deck
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining = [c for c in all_cards if c not in hand]
    
    if len(remaining) == 0:
        return "STAY"
    
    # Calculate probability of not busting and expected score if we hit
    safe_scores = []
    for card in remaining:
        new_hand = hand + [card]
        new_val = hand_value(new_hand, target)
        if new_val <= target:
            safe_scores.append(new_val)
    
    n_remaining = len(remaining)
    n_safe = len(safe_scores)
    p_safe = n_safe / n_remaining
    
    # If no safe cards, stay
    if n_safe == 0:
        return "STAY"
    
    # Expected score if we hit and don't bust
    expected_if_hit_safe = sum(safe_scores) / n_safe
    
    # Gap to target
    gap = target - current
    
    # Calculate expected value comparison
    # If we stay: our score is 'current'
    # If we hit: p_safe * expected_if_hit_safe + (1 - p_safe) * (bust = very bad)
    
    # Against a good opponent, we need to be close to target to win
    # Busting is very bad (guaranteed loss unless opponent also busts)
    
    # Heuristic: consider the value of hitting
    # Assume busting gives us a score of 0 effectively for comparison
    # We hit if expected improvement (with risk) is worth it
    
    # More aggressive when far from target, more conservative when close
    
    # Expected score if we hit (treating bust as losing position)
    # For now, let's use a threshold-based approach
    
    # Dynamic threshold based on gap and bust probability
    if gap >= 5:
        # Far from target, hit unless very likely to bust
        if p_safe >= 0.25:
            return "HIT"
    elif gap >= 4:
        if p_safe >= 0.35:
            return "HIT"
    elif gap >= 3:
        if p_safe >= 0.45:
            return "HIT"
    elif gap >= 2:
        if p_safe >= 0.55:
            return "HIT"
    elif gap >= 1:
        if p_safe >= 0.65:
            return "HIT"
    
    return "STAY"
