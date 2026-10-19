
def policy(hand: list[str], target: int) -> str:
    ALL_CARDS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    
    def card_value(card):
        if card in ['J', 'Q', 'K']:
            return 10
        elif card == 'A':
            return 11  # Will be adjusted
        else:
            return int(card)
    
    def calculate_value(cards, target):
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
        
        # Adjust aces if over target
        while value > target and aces > 0:
            value -= 10
            aces -= 1
        
        return value
    
    def count_aces(cards):
        return sum(1 for c in cards if c == 'A')
    
    # Get remaining cards in deck
    remaining = []
    for card in ALL_CARDS:
        if card not in hand:
            remaining.append(card)
    
    current_value = calculate_value(hand, target)
    
    # If already at or over target, stay (or we've busted)
    if current_value >= target:
        return "STAY"
    
    # Calculate expected value using dynamic programming with memoization
    # State: (current_value, aces_as_11, frozenset of remaining cards)
    
    from functools import lru_cache
    
    def get_state_value(cards_in_hand, remaining_cards):
        """Get value and number of aces counting as 11"""
        value = 0
        aces_as_11 = 0
        for card in cards_in_hand:
            if card == 'A':
                value += 11
                aces_as_11 += 1
            elif card in ['J', 'Q', 'K']:
                value += 10
            else:
                value += int(card)
        
        while value > target and aces_as_11 > 0:
            value -= 10
            aces_as_11 -= 1
        
        return value, aces_as_11
    
    @lru_cache(maxsize=None)
    def expected_value(value, aces_as_11, remaining_tuple):
        """Calculate optimal expected value from this state"""
        remaining_list = list(remaining_tuple)
        
        if value > target:
            return -1  # Busted (use -1 to indicate loss)
        
        if not remaining_list:
            return value  # No more cards
        
        # Value of staying
        stay_value = value
        
        # Value of hitting - average over all remaining cards
        hit_values = []
        for card in remaining_list:
            new_remaining = tuple(c for c in remaining_list if c != card)
            
            # Calculate new value
            if card == 'A':
                new_value = value + 11
                new_aces = aces_as_11 + 1
            elif card in ['J', 'Q', 'K']:
                new_value = value + 10
                new_aces = aces_as_11
            else:
                new_value = value + int(card)
                new_aces = aces_as_11
            
            # Adjust aces
            while new_value > target and new_aces > 0:
                new_value -= 10
                new_aces -= 1
            
            if new_value > target:
                hit_values.append(-1)  # Bust
            else:
                hit_values.append(expected_value(new_value, new_aces, new_remaining))
        
        avg_hit_value = sum(hit_values) / len(hit_values)
        
        return max(stay_value, avg_hit_value)
    
    # Calculate expected value of hitting
    hit_values = []
    current_aces_11 = 0
    temp_value = 0
    for card in hand:
        if card == 'A':
            temp_value += 11
            current_aces_11 += 1
        elif card in ['J', 'Q', 'K']:
            temp_value += 10
        else:
            temp_value += int(card)
    while temp_value > target and current_aces_11 > 0:
        temp_value -= 10
        current_aces_11 -= 1
    
    for card in remaining:
        new_remaining = tuple(c for c in remaining if c != card)
        
        if card == 'A':
            new_value = current_value + 11
            new_aces = current_aces_11 + 1
        elif card in ['J', 'Q', 'K']:
            new_value = current_value + 10
            new_aces = current_aces_11
        else:
            new_value = current_value + int(card)
            new_aces = current_aces_11
        
        while new_value > target and new_aces > 0:
            new_value -= 10
            new_aces -= 1
        
        if new_value > target:
            hit_values.append(-1)
        else:
            hit_values.append(expected_value(new_value, new_aces, new_remaining))
    
    avg_hit_value = sum(hit_values) / len(hit_values)
    
    if avg_hit_value > current_value:
        return "HIT"
    else:
        return "STAY"
