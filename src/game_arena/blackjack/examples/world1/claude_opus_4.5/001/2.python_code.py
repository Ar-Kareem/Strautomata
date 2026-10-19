
def policy(hand: list[str], target: int) -> str:
    def card_value(card):
        if card in ['J', 'Q', 'K']:
            return 10
        elif card == 'A':
            return 11
        else:
            return int(card)
    
    def hand_value(cards, t):
        total = sum(card_value(c) for c in cards)
        aces = cards.count('A')
        while total > t and aces > 0:
            total -= 10
            aces -= 1
        return total
    
    current_value = hand_value(hand, target)
    
    # If we've reached or exceeded target, stay
    if current_value >= target:
        return "STAY"
    
    # Cards remaining in our deck
    all_cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    remaining = [c for c in all_cards if c not in hand]
    
    if not remaining:
        return "STAY"
    
    # Calculate outcomes if we hit
    bust_count = 0
    safe_values = []
    
    for card in remaining:
        new_hand = hand + [card]
        new_value = hand_value(new_hand, target)
        if new_value > target:
            bust_count += 1
        else:
            safe_values.append(new_value)
    
    n_remaining = len(remaining)
    p_bust = bust_count / n_remaining
    
    # If we'd always bust, stay
    if not safe_values:
        return "STAY"
    
    expected_if_hit_safe = sum(safe_values) / len(safe_values)
    
    # Gap to target
    gap = target - current_value
    
    # Expected value calculation for hitting
    # If we bust, we get -infinity (lose), so we model expected value
    # Assuming opponent achieves around target - 3 on average
    
    # Heuristic thresholds based on gap and bust probability
    # The idea: stay if we're close to target and bust risk is significant
    
    # Dynamic threshold: as we get closer to target, be more conservative
    if gap <= 1:
        return "STAY"
    
    if gap == 2 and p_bust > 0.15:
        return "STAY"
    
    if gap == 3 and p_bust > 0.35:
        return "STAY"
    
    if gap == 4 and p_bust > 0.50:
        return "STAY"
    
    if gap == 5 and p_bust > 0.60:
        return "STAY"
    
    if gap >= 6 and p_bust > 0.70:
        return "STAY"
    
    # Calculate expected value more precisely
    # Value of staying: current_value
    # Value of hitting: (1-p_bust) * expected_if_hit_safe + p_bust * (loss value)
    # If opponent has expected score around target-3, staying at current_value
    # has some win probability
    
    # Simplified model: hitting is worth it if expected improvement outweighs bust risk
    expected_improvement = expected_if_hit_safe - current_value
    
    # Weight bust risk vs improvement
    # A rough model: we lose if we bust, so busting is very bad
    # If p_bust is high, we need large improvement to justify
    
    if p_bust > 0.5:
        # Only hit if we're far from target
        if gap > 5:
            return "HIT"
        else:
            return "STAY"
    
    # Default: hit if gap is significant
    return "HIT"
