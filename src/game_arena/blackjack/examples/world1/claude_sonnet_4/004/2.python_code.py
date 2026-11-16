
def policy(hand: list[str], target: int) -> str:
    def calculate_hand_value(cards, target_score):
        """Calculate the optimal value of a hand given the target."""
        value = 0
        aces = 0
        
        for card in cards:
            if card == "A":
                aces += 1
            elif card in ["J", "Q", "K"]:
                value += 10
            else:
                value += int(card)
        
        # Add aces optimally - as many 11s as possible without busting
        for _ in range(aces):
            if value + 11 <= target_score:
                value += 11
            else:
                value += 1
        
        return value
    
    def get_remaining_cards(hand):
        """Get the list of cards remaining in deck."""
        all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        remaining = []
        hand_set = set(hand)
        
        for card in all_cards:
            if card not in hand_set:
                remaining.append(card)
        
        return remaining
    
    def card_value(card, current_value, target_score):
        """Get the value a card would add to current hand."""
        if card == "A":
            # Ace is 11 if it doesn't bust us, otherwise 1
            return 11 if current_value + 11 <= target_score else 1
        elif card in ["J", "Q", "K"]:
            return 10
        else:
            return int(card)
    
    # Calculate current hand value
    current_value = calculate_hand_value(hand, target)
    
    # If we're already at a good score, be more conservative
    if current_value >= target:
        return "STAY"
    
    # Get remaining cards
    remaining_cards = get_remaining_cards(hand)
    
    if not remaining_cards:
        return "STAY"
    
    # Calculate bust probability and expected value
    bust_count = 0
    total_improvement = 0
    
    for card in remaining_cards:
        card_val = card_value(card, current_value, target)
        new_value = current_value + card_val
        
        if new_value > target:
            bust_count += 1
        else:
            # Calculate how much this improves our position
            improvement = new_value - current_value
            total_improvement += improvement
    
    bust_probability = bust_count / len(remaining_cards)
    avg_improvement = total_improvement / len(remaining_cards) if remaining_cards else 0
    
    # Decision logic based on multiple factors
    
    # If bust probability is too high, stay
    if bust_probability > 0.4:
        return "STAY"
    
    # If we're very close to target, be conservative
    distance_to_target = target - current_value
    if distance_to_target <= 2:
        return "STAY"
    
    # For different target ranges, use different thresholds
    if target <= 15:
        # Lower targets - be more conservative
        threshold = target * 0.8
    elif target <= 21:
        # Medium targets - standard aggressive play
        threshold = target * 0.75
    else:
        # High targets - can be more aggressive early
        threshold = target * 0.7
    
    # If we're below threshold and bust probability is reasonable, hit
    if current_value < threshold:
        return "HIT"
    
    # For edge cases, consider expected value
    # If expected improvement is good and bust probability is low, hit
    if avg_improvement >= 3 and bust_probability <= 0.25:
        return "HIT"
    
    return "STAY"
