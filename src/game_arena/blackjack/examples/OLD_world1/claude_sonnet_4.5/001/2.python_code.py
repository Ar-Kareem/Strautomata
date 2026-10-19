
def policy(hand: list[str], target: int) -> str:
    """
    Policy for simplified Blackjack-like game.
    
    Strategy:
    - Calculate current hand value
    - Estimate opponent's likely stopping point
    - Use dynamic threshold based on target and risk assessment
    """
    
    def card_value(card: str, current_sum: int, target: int) -> int:
        """Calculate the value of a card given current hand state."""
        if card in ["J", "Q", "K"]:
            return 10
        elif card == "A":
            # A is 11 if it keeps us at or below target, else 1
            return 11 if current_sum + 11 <= target else 1
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
    
    def expected_next_card_value(hand: list[str], target: int) -> float:
        """Calculate expected value of next card from remaining deck."""
        # All cards in deck
        all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        
        # Cards already in hand
        remaining = [c for c in all_cards if c not in hand]
        
        if not remaining:
            return 0
        
        current = hand_value(hand, target)
        total_value = 0
        
        for card in remaining:
            total_value += card_value(card, current, target)
        
        return total_value / len(remaining)
    
    def bust_probability(hand: list[str], target: int) -> float:
        """Calculate probability of busting on next card."""
        all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        remaining = [c for c in all_cards if c not in hand]
        
        if not remaining:
            return 1.0
        
        current = hand_value(hand, target)
        bust_count = 0
        
        for card in remaining:
            next_val = card_value(card, current, target)
            if current + next_val > target:
                bust_count += 1
        
        return bust_count / len(remaining)
    
    current_value = hand_value(hand, target)
    
    # If we've already busted, stay (shouldn't happen but safety check)
    if current_value > target:
        return "STAY"
    
    # If we have all cards, must stay
    if len(hand) >= 13:
        return "STAY"
    
    # Calculate metrics
    bp = bust_probability(hand, target)
    expected_card = expected_next_card_value(hand, target)
    
    # Dynamic threshold based on target
    # Higher targets allow more aggressive play
    # Base threshold: aim for 85-90% of target
    base_threshold_ratio = 0.85 + (target - 10) / 200.0  # Slightly more aggressive for higher targets
    base_threshold = target * base_threshold_ratio
    
    # Adjust threshold based on bust probability
    # If bust probability is low, we can be more aggressive
    if bp < 0.2:
        # Low risk, can aim higher
        threshold = min(target - 1, base_threshold + 2)
    elif bp < 0.4:
        # Moderate risk
        threshold = base_threshold
    elif bp < 0.6:
        # High risk, be conservative
        threshold = base_threshold - 1
    else:
        # Very high risk, be very conservative
        threshold = base_threshold - 2
    
    # Special case: if we're very close to target and have low bust probability
    if current_value >= target - 3 and bp < 0.3:
        if current_value + expected_card <= target:
            return "HIT"
        else:
            return "STAY"
    
    # Main decision logic
    if current_value < threshold:
        # We're below threshold, should hit if reasonable
        if bp < 0.5:  # Less than 50% chance of busting
            return "HIT"
        elif current_value < target - 5:  # Far from target, take some risk
            return "HIT"
        else:
            return "STAY"
    else:
        # We're at or above threshold
        if bp < 0.25 and current_value < target - 1:  # Very safe and not at target yet
            return "HIT"
        else:
            return "STAY"
