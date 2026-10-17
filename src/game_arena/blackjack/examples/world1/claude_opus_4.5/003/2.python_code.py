
def policy(hand: list[str], target: int) -> str:
    from functools import lru_cache
    
    def get_card_value(card):
        if card in ['J', 'Q', 'K']:
            return 10
        elif card == 'A':
            return 11  # Will adjust later
        else:
            return int(card)
    
    def compute_hand_value(cards):
        total = 0
        aces = 0
        for c in cards:
            if c == 'A':
                total += 11
                aces += 1
            elif c in ['J', 'Q', 'K']:
                total += 10
            else:
                total += int(c)
        while total > target and aces > 0:
            total -= 10
            aces -= 1
        return total, aces
    
    current_value, current_aces = compute_hand_value(hand)
    
    if current_value >= target:
        return "STAY"
    
    if current_value > target:  # Already busted (shouldn't happen)
        return "STAY"
    
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining = tuple(sorted(c for c in all_cards if c not in hand))
    
    # Use DP to compute optimal expected score from any state
    # State: (current_value, aces_as_11, remaining_cards_tuple)
    # Returns: expected best achievable score (or -infinity if bust)
    
    @lru_cache(maxsize=None)
    def optimal_expected(value, aces, remaining_cards):
        if value > target:
            return -1000  # Busted - very bad
        
        if not remaining_cards:
            return value  # No more cards to draw
        
        # Option 1: Stay with current value
        stay_score = value
        
        # Option 2: Hit and continue optimally
        total_hit_score = 0
        n = len(remaining_cards)
        
        for i, card in enumerate(remaining_cards):
            new_remaining = remaining_cards[:i] + remaining_cards[i+1:]
            
            if card == 'A':
                card_val = 11
                new_aces = aces + 1
            elif card in ['J', 'Q', 'K']:
                card_val = 10
                new_aces = aces
            else:
                card_val = int(card)
                new_aces = aces
            
            new_value = value + card_val
            
            # Adjust aces if over target
            while new_value > target and new_aces > 0:
                new_value -= 10
                new_aces -= 1
            
            total_hit_score += optimal_expected(new_value, new_aces, new_remaining)
        
        hit_expected = total_hit_score / n
        
        return max(stay_score, hit_expected)
    
    # Now decide: should we hit or stay?
    stay_score = current_value
    
    # Calculate expected score if we hit
    total_hit_score = 0
    n = len(remaining)
    
    for i, card in enumerate(remaining):
        new_remaining = remaining[:i] + remaining[i+1:]
        
        if card == 'A':
            card_val = 11
            new_aces = current_aces + 1
        elif card in ['J', 'Q', 'K']:
            card_val = 10
            new_aces = current_aces
        else:
            card_val = int(card)
            new_aces = current_aces
        
        new_value = current_value + card_val
        
        while new_value > target and new_aces > 0:
            new_value -= 10
            new_aces -= 1
        
        total_hit_score += optimal_expected(new_value, new_aces, new_remaining)
    
    hit_expected = total_hit_score / n
    
    if hit_expected > stay_score:
        return "HIT"
    else:
        return "STAY"
