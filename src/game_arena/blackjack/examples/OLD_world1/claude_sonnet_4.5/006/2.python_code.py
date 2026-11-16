
def policy(hand: list[str], target: int) -> str:
    """
    Policy for simplified Blackjack-like game.
    
    Strategy:
    - Calculate current hand value
    - Estimate probability of busting on next card
    - Estimate opponent's likely final score
    - Make decision based on risk/reward
    """
    
    def card_value(card: str, current_sum: int, target: int) -> int:
        """Calculate the value of a card given current hand state."""
        if card in ["J", "Q", "K"]:
            return 10
        elif card == "A":
            # Ace is 11 if it doesn't bust, otherwise 1
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
    
    def remaining_cards(hand: list[str]) -> list[str]:
        """Get list of cards not yet drawn."""
        all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        remaining = []
        hand_set = set(hand)
        for card in all_cards:
            if card not in hand_set:
                remaining.append(card)
        return remaining
    
    current_value = hand_value(hand, target)
    
    # If we're already at or very close to target, stay
    if current_value >= target:
        return "STAY"
    
    # Get remaining cards
    remaining = remaining_cards(hand)
    
    if len(remaining) == 0:
        return "STAY"
    
    # Calculate bust probability and expected value
    bust_count = 0
    expected_values = []
    
    for card in remaining:
        value = card_value(card, current_value, target)
        new_total = current_value + value
        
        if new_total > target:
            bust_count += 1
        else:
            expected_values.append(new_total)
    
    bust_prob = bust_count / len(remaining)
    
    # Expected opponent score (they play optimally too)
    # Rough estimate: opponent tends to reach around target - 3 to target
    expected_opponent = target - 2
    
    # Decision logic
    gap = target - current_value
    
    # If we're very far from target, always hit
    if gap >= 10:
        return "HIT"
    
    # If bust probability is too high, stay
    if bust_prob > 0.5:
        return "STAY"
    
    # If we have a good chance to improve and we're below expected opponent score
    if current_value < expected_opponent - 2 and bust_prob < 0.4:
        return "HIT"
    
    # Strategic threshold based on target
    # Lower targets need more conservative play
    if target <= 15:
        threshold = target - 2
    elif target <= 20:
        threshold = target - 3
    else:
        threshold = target - 4
    
    # If we're below threshold and bust risk is acceptable, hit
    if current_value < threshold and bust_prob < 0.6:
        return "HIT"
    
    # Conservative play when close to target
    if gap <= 3:
        # Only hit if very low bust risk
        if bust_prob < 0.3:
            return "HIT"
        else:
            return "STAY"
    
    # Medium gap - balance risk/reward
    if gap <= 6:
        if bust_prob < 0.45:
            return "HIT"
        else:
            return "STAY"
    
    # Default: hit if reasonable bust probability
    if bust_prob < 0.5:
        return "HIT"
    
    return "STAY"
