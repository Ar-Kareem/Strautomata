
def policy(hand: list[str], target: int) -> str:
    """
    Policy for simplified Blackjack-like game.
    
    Strategy:
    - Calculate current hand value
    - Estimate probability of busting with next card
    - Consider expected value of hitting vs staying
    - Account for what opponent might do
    """
    
    def card_value(card: str, current_sum: int, target: int) -> int:
        """Calculate the value of a card given current hand state."""
        if card in ["J", "Q", "K"]:
            return 10
        elif card == "A":
            # Use 11 if it doesn't bust, otherwise 1
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
            if card == "A":
                aces += 1
                total += 11
            elif card in ["J", "Q", "K"]:
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
    
    # If we hit target exactly, stay
    if current_value == target:
        return "STAY"
    
    remaining_cards = get_remaining_cards(hand)
    
    if not remaining_cards:
        return "STAY"
    
    # Calculate probability of busting and expected value of next card
    bust_count = 0
    safe_values = []
    
    for card in remaining_cards:
        next_value = current_value + card_value(card, current_value, target)
        if next_value > target:
            bust_count += 1
        else:
            safe_values.append(next_value)
    
    num_remaining = len(remaining_cards)
    bust_prob = bust_count / num_remaining if num_remaining > 0 else 1.0
    
    # Conservative threshold based on target
    # Higher targets allow more risk, but we generally want to be conservative
    
    # Calculate the gap to target
    gap = target - current_value
    
    # If gap is very small (1-3), be very conservative
    if gap <= 3:
        # Only hit if very low chance of busting
        if bust_prob <= 0.2:
            return "HIT"
        else:
            return "STAY"
    
    # For medium gaps (4-7), balance risk
    if gap <= 7:
        if bust_prob <= 0.4:
            return "HIT"
        else:
            return "STAY"
    
    # For larger gaps, be more aggressive but still cautious
    # We need to get closer to target
    if current_value < target * 0.65:
        # We're far from target, hit unless very risky
        if bust_prob <= 0.6:
            return "HIT"
        else:
            return "STAY"
    elif current_value < target * 0.75:
        if bust_prob <= 0.5:
            return "HIT"
        else:
            return "STAY"
    elif current_value < target * 0.85:
        if bust_prob <= 0.4:
            return "HIT"
        else:
            return "STAY"
    else:
        # We're close to target (>=85%), be conservative
        if bust_prob <= 0.3:
            return "HIT"
        else:
            return "STAY"
