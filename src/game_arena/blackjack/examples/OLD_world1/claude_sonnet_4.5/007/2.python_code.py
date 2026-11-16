
def policy(hand: list[str], target: int) -> str:
    """
    Policy for simplified Blackjack-like game.
    
    Strategy:
    - Calculate current hand value
    - Estimate probability of busting on next card
    - Estimate opponent's likely score
    - Make optimal decision based on expected value
    """
    
    def card_value(card: str, current_sum: int, target: int) -> int:
        """Calculate the value of a single card given current hand state."""
        if card in ['J', 'Q', 'K']:
            return 10
        elif card == 'A':
            # Ace is 11 if it doesn't cause us to exceed target, else 1
            if current_sum + 11 <= target:
                return 11
            else:
                return 1
        else:
            return int(card)
    
    def hand_value(cards: list[str], target: int) -> int:
        """Calculate total value of hand."""
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
        
        # Adjust aces from 11 to 1 if needed
        while total > target and aces > 0:
            total -= 10
            aces -= 1
        
        return total
    
    def get_remaining_cards(hand: list[str]) -> list[str]:
        """Get list of cards not yet drawn from our deck."""
        all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        remaining = []
        hand_copy = hand.copy()
        
        for card in all_cards:
            if card in hand_copy:
                hand_copy.remove(card)
            else:
                remaining.append(card)
        
        return remaining
    
    current_value = hand_value(hand, target)
    
    # If we've busted, we already lost (shouldn't happen with proper play)
    if current_value > target:
        return "STAY"
    
    # Get remaining cards in our deck
    remaining = get_remaining_cards(hand)
    
    if len(remaining) == 0:
        return "STAY"
    
    # Calculate probabilities and expected outcomes
    bust_count = 0
    total_gain = 0
    
    for card in remaining:
        # What would our value be if we draw this card?
        test_hand = hand + [card]
        new_value = hand_value(test_hand, target)
        
        if new_value > target:
            bust_count += 1
        else:
            # Gain is how much closer we get to target
            total_gain += (new_value - current_value)
    
    prob_bust = bust_count / len(remaining)
    
    # Estimate opponent's expected score
    # Opponent plays optimally from same deck, so they'll likely get close to target
    # Conservative estimate: opponent gets to around target - 3 on average
    estimated_opponent_score = target - 3
    
    # Decision logic
    margin = target - current_value
    
    # If we're very close to target (within 2), stay
    if margin <= 2:
        return "STAY"
    
    # If we're far from target and low bust risk, hit
    if margin >= 7 and prob_bust < 0.4:
        return "HIT"
    
    # If we're likely behind the opponent estimate and have low bust risk, hit
    if current_value < estimated_opponent_score and prob_bust < 0.5:
        return "HIT"
    
    # If bust probability is too high, stay
    if prob_bust > 0.5:
        return "STAY"
    
    # Middle ground: hit if we're not too close and bust risk is reasonable
    if margin > 4 and prob_bust < 0.45:
        return "HIT"
    
    # Default: stay if we're reasonably close
    if margin <= 5:
        return "STAY"
    
    # Otherwise hit
    return "HIT"
