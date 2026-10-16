
def policy(hand: list[str], target: int) -> str:
    """
    Policy for simplified Blackjack-like game.
    
    Args:
        hand: List of card strings currently held
        target: Target score to approach without exceeding
    
    Returns:
        "HIT" or "STAY"
    """
    
    def hand_value(cards, target):
        """Calculate the value of a hand, handling Aces optimally."""
        total = 0
        aces = 0
        
        for card in cards:
            if card == "A":
                aces += 1
            elif card in ["J", "Q", "K"]:
                total += 10
            else:
                total += int(card)
        
        # Add aces - use 11 when it doesn't cause bust, otherwise 1
        for _ in range(aces):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
        
        return total
    
    def card_base_value(card):
        """Get the minimum value a card can contribute."""
        if card == "A":
            return 1  # Minimum value
        elif card in ["J", "Q", "K"]:
            return 10
        else:
            return int(card)
    
    # Calculate current hand value
    current_value = hand_value(hand, target)
    
    # If already busted, must STAY (shouldn't happen in valid game)
    if current_value > target:
        return "STAY"
    
    # Determine remaining cards in deck
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining = [card for card in all_cards if card not in hand]
    
    # If no cards left, must STAY
    if not remaining:
        return "STAY"
    
    # Calculate bust probability and expected outcomes
    bust_count = 0
    safe_count = 0
    
    for card in remaining:
        # Calculate value this card would add
        if card == "A":
            card_val = 11 if current_value + 11 <= target else 1
        elif card in ["J", "Q", "K"]:
            card_val = 10
        else:
            card_val = int(card)
        
        new_value = current_value + card_val
        
        if new_value > target:
            bust_count += 1
        else:
            safe_count += 1
    
    bust_probability = bust_count / len(remaining)
    
    # Strategy: Use a threshold that adapts to the target
    # Generally, stand when close enough to target or when risk is too high
    
    # If we're very close to target (within 2), STAY
    if current_value >= target - 2:
        return "STAY"
    
    # If we have a decent score (>= 75% of target) and bust risk > 40%, STAY
    if current_value >= target * 0.75 and bust_probability > 0.4:
        return "STAY"
    
    # If we have a good score (>= 85% of target) and bust risk > 30%, STAY  
    if current_value >= target * 0.85 and bust_probability > 0.3:
        return "STAY"
    
    # If bust probability is very high (> 60%), STAY
    if bust_probability > 0.6:
        return "STAY"
    
    # Otherwise, HIT to try to get closer to target
    return "HIT"
