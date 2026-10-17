
def policy(hand: list[str], target: int) -> str:
    all_cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    
    def hand_value(cards):
        """Calculate hand value, handling Aces optimally"""
        total = 0
        aces = 0
        for card in cards:
            if card in ['J', 'Q', 'K']:
                total += 10
            elif card == 'A':
                aces += 1
            else:
                total += int(card)
        
        # Add aces - greedily use 11 if possible
        for _ in range(aces):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
        
        return total
    
    def expected_score(current_cards, remaining_cards, memo=None):
        """Calculate expected optimal score given current state"""
        if memo is None:
            memo = {}
        
        key = (tuple(sorted(current_cards)), tuple(sorted(remaining_cards)))
        if key in memo:
            return memo[key]
        
        current_val = hand_value(current_cards)
        
        # If busted, return a low score
        if current_val > target:
            return -1  # Busted
        
        # If no more cards to draw, must stay
        if not remaining_cards:
            return current_val
        
        # Expected value if we hit
        hit_value = 0
        for i, card in enumerate(remaining_cards):
            new_hand = current_cards + [card]
            new_remaining = remaining_cards[:i] + remaining_cards[i+1:]
            card_score = expected_score(new_hand, new_remaining, memo)
            hit_value += card_score
        hit_value /= len(remaining_cards)
        
        # Best of staying or hitting
        result = max(current_val, hit_value)
        memo[key] = result
        return result
    
    current_value = hand_value(hand)
    
    # If at or above target, stay
    if current_value >= target:
        return "STAY"
    
    # Calculate remaining cards in deck
    remaining = list(all_cards)
    for card in hand:
        if card in remaining:
            remaining.remove(card)
    
    if not remaining:
        return "STAY"
    
    # Calculate expected value of hitting
    hit_expected = 0
    bust_count = 0
    stay_better_count = 0
    
    for i, card in enumerate(remaining):
        new_hand = hand + [card]
        new_remaining = remaining[:i] + remaining[i+1:]
        new_value = hand_value(new_hand)
        
        if new_value > target:
            # Busted - use a penalty value
            hit_expected += -1
            bust_count += 1
        else:
            # Calculate optimal expected score from this state
            card_expected = expected_score(new_hand, new_remaining, {})
            hit_expected += card_expected
            if card_expected <= current_value:
                stay_better_count += 1
    
    hit_expected /= len(remaining)
    
    # Compare staying (current value) vs hitting (expected value)
    # Account for the fact that busting is very bad
    if hit_expected > current_value:
        return "HIT"
    else:
        return "STAY"
