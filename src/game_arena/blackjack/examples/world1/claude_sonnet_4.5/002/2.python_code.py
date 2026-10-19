
def policy(hand: list[str], target: int) -> str:
    """
    Policy for simplified Blackjack with variable target.
    Returns "HIT" or "STAY" based on current hand and target.
    """
    
    def calculate_hand_value(hand, target):
        """Calculate the value of the current hand."""
        non_ace_sum = 0
        ace_count = 0
        
        for card in hand:
            if card == 'A':
                ace_count += 1
            elif card in ['J', 'Q', 'K']:
                non_ace_sum += 10
            else:
                non_ace_sum += int(card)
        
        # Add aces optimally (as 11 when possible, otherwise 1)
        total = non_ace_sum
        for _ in range(ace_count):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
        
        return total
    
    def get_remaining_cards(hand):
        """Determine which cards haven't been drawn yet."""
        all_cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        remaining = []
        hand_copy = hand.copy()
        
        for card in all_cards:
            if card in hand_copy:
                hand_copy.remove(card)
            else:
                remaining.append(card)
        
        return remaining
    
    current_value = calculate_hand_value(hand, target)
    
    # If we've met or exceeded target, must STAY
    if current_value >= target:
        return "STAY"
    
    # Get remaining cards
    remaining = get_remaining_cards(hand)
    
    # If no cards left (edge case), STAY
    if len(remaining) == 0:
        return "STAY"
    
    # Calculate bust probability and expected value
    bust_count = 0
    total_value_if_safe = 0
    safe_count = 0
    
    for card in remaining:
        # Determine card value
        if card in ['J', 'Q', 'K']:
            value = 10
        elif card == 'A':
            # Ace is 11 if it doesn't bust, else 1
            value = 11 if current_value + 11 <= target else 1
        else:
            value = int(card)
        
        new_total = current_value + value
        
        if new_total > target:
            bust_count += 1
        else:
            safe_count += 1
            total_value_if_safe += new_total
    
    bust_prob = bust_count / len(remaining)
    
    # Decision strategy
    gap = target - current_value
    
    # If bust probability is very high (>60%), STAY
    if bust_prob > 0.6:
        return "STAY"
    
    # If we're very close to target (within 3), be conservative
    if gap <= 3 and bust_prob > 0.3:
        return "STAY"
    
    # If gap is small (1-2), STAY
    if gap <= 2:
        return "STAY"
    
    # If we have good odds and significant gap, HIT
    if bust_prob < 0.5 and gap >= 4:
        return "HIT"
    
    # Default: if gap >= 5, HIT; otherwise STAY
    return "HIT" if gap >= 5 else "STAY"
