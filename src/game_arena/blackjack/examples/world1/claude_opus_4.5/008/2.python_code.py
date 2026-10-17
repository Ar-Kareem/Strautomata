
def policy(hand: list[str], target: int) -> str:
    def card_value(card):
        if card in ['J', 'Q', 'K']:
            return 10
        elif card == 'A':
            return 11  # Will handle soft value separately
        else:
            return int(card)
    
    def calculate_hand_value(hand, target):
        value = 0
        aces = 0
        for card in hand:
            if card == 'A':
                aces += 1
            elif card in ['J', 'Q', 'K']:
                value += 10
            else:
                value += int(card)
        
        # Add aces - try to use 11 first, then downgrade to 1 if needed
        for _ in range(aces):
            if value + 11 <= target:
                value += 11
            else:
                value += 1
        
        return value
    
    current_value = calculate_hand_value(hand, target)
    
    # If we've hit target exactly or busted, stay (busting case doesn't matter)
    if current_value >= target:
        return "STAY"
    
    # Determine remaining cards in deck
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining = [c for c in all_cards if c not in hand]
    
    if not remaining:
        return "STAY"
    
    # Calculate probability of busting and expected value if we hit
    bust_count = 0
    total_value_if_not_bust = 0
    not_bust_count = 0
    
    for card in remaining:
        new_hand = hand + [card]
        new_value = calculate_hand_value(new_hand, target)
        if new_value > target:
            bust_count += 1
        else:
            not_bust_count += 1
            total_value_if_not_bust += new_value
    
    bust_prob = bust_count / len(remaining)
    
    # Expected value if we hit and don't bust
    if not_bust_count > 0:
        avg_value_if_not_bust = total_value_if_not_bust / not_bust_count
    else:
        avg_value_if_not_bust = 0
    
    # Decision logic:
    # Stay if bust probability is too high relative to potential gain
    # Also consider how far we are from target
    
    gap = target - current_value
    
    # If very close to target (within 3) and bust prob > 40%, stay
    # If further from target, be more aggressive
    
    # Simple expected value comparison:
    # E[stay] ~ current_value (simplified - assumes we win if opponent busts or has less)
    # E[hit] ~ (1 - bust_prob) * avg_value_if_not_bust
    
    # But we should also consider that staying at low value often loses
    # Let's use a threshold approach based on gap and bust probability
    
    # If current value is decent (close to target) and bust risk is significant, stay
    if gap <= 0:
        return "STAY"
    
    # Calculate the threshold dynamically
    # We want to hit if expected improvement outweighs bust risk
    
    # Simple heuristic: hit if expected value of hitting beats staying
    # Rough approximation: staying at value V wins about V/T of the time against random opponent
    # hitting and not busting gives us avg_value_if_not_bust
    
    # Simplified decision: 
    # E[hit] = (1 - bust_prob) * (value gained by not busting outcome on average)
    # Compare this to risk of busting
    
    # Key insight: if we're far below target, we likely lose by staying
    # So we should be aggressive when current_value is low
    
    min_competitive_value = target - 4  # Heuristic: need to be within 4 of target to be competitive
    
    if current_value < min_competitive_value:
        # We're not competitive, should hit unless bust is almost certain
        if bust_prob < 0.85:
            return "HIT"
        else:
            return "STAY"
    
    # We're competitive - be more conservative
    # Stay if bust probability is significant
    if bust_prob > 0.5:
        return "STAY"
    
    # Stay if we're very close to target
    if gap <= 2 and bust_prob > 0.3:
        return "STAY"
    
    # Otherwise hit to try to improve
    return "HIT"
