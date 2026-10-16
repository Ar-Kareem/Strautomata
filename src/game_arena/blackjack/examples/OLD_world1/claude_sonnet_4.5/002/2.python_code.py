
def policy(hand: list[str], target: int) -> str:
    """
    Policy for simplified Blackjack-like game.
    
    Strategy:
    - Calculate current hand value
    - Estimate probability of busting on next card
    - Consider opponent's expected behavior
    - Make risk-adjusted decision based on target and current value
    """
    
    def card_value(card: str, current_sum: int, target: int) -> int:
        """Calculate the value of a single card given current hand state."""
        if card in ['J', 'Q', 'K']:
            return 10
        elif card == 'A':
            # Ace is 11 if it doesn't bust, otherwise 1
            return 11 if current_sum + 11 <= target else 1
        else:
            return int(card)
    
    def hand_value(cards: list[str], target: int) -> int:
        """Calculate total value of hand with optimal Ace handling."""
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
        
        # Convert Aces from 11 to 1 if busting
        while total > target and aces > 0:
            total -= 10
            aces -= 1
        
        return total
    
    def get_remaining_cards(hand: list[str]) -> list[str]:
        """Get list of cards not yet drawn from our deck."""
        all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        remaining = []
        hand_set = list(hand)  # Make a copy
        
        for card in all_cards:
            if card not in hand_set:
                remaining.append(card)
            else:
                hand_set.remove(card)  # Remove only one instance
        
        return remaining
    
    def expected_card_value(remaining: list[str], current_sum: int, target: int) -> float:
        """Calculate expected value of next card."""
        if not remaining:
            return 0
        
        total = 0
        for card in remaining:
            total += card_value(card, current_sum, target)
        
        return total / len(remaining)
    
    def bust_probability(hand: list[str], current_sum: int, target: int) -> float:
        """Calculate probability of busting on next card."""
        remaining = get_remaining_cards(hand)
        
        if not remaining:
            return 1.0
        
        bust_count = 0
        for card in remaining:
            next_value = card_value(card, current_sum, target)
            if current_sum + next_value > target:
                bust_count += 1
        
        return bust_count / len(remaining)
    
    current_sum = hand_value(hand, target)
    
    # If we've busted, we should have stayed earlier, but return STAY
    if current_sum > target:
        return "STAY"
    
    # If we've hit the target exactly, stay
    if current_sum == target:
        return "STAY"
    
    remaining = get_remaining_cards(hand)
    
    # If no cards left, must stay
    if not remaining:
        return "STAY"
    
    # Calculate bust probability
    bust_prob = bust_probability(hand, current_sum, target)
    
    # Calculate gap to target
    gap = target - current_sum
    
    # Strategy based on multiple factors:
    # 1. If gap is very small, be conservative
    # 2. If bust probability is high, be conservative
    # 3. Consider how close we are to target as percentage
    
    # Calculate expected opponent final score (they use similar strategy)
    # Opponent is expected to get close to target, assume around target - 2 to target
    # More aggressive if we're far from target
    
    threshold_score = target - 3
    
    # Adjust threshold based on target value
    if target <= 15:
        threshold_score = target - 2
    elif target >= 25:
        threshold_score = target - 4
    
    # If current sum is below threshold and bust probability is reasonable, hit
    if current_sum < threshold_score and bust_prob < 0.5:
        return "HIT"
    
    # If we're very far from target and bust prob is low, keep hitting
    if gap >= 7 and bust_prob < 0.3:
        return "HIT"
    
    # If we're reasonably close and bust probability is high, stay
    if gap <= 5 and bust_prob > 0.4:
        return "STAY"
    
    # Middle ground: hit if bust probability is acceptable
    if bust_prob < 0.35:
        return "HIT"
    
    return "STAY"
