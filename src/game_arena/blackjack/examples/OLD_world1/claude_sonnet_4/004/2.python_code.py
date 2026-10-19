
def policy(hand: list[str], target: int) -> str:
    def card_value(card: str, current_sum: int, target: int) -> int:
        """Calculate the value of a card given the current hand sum and target."""
        if card in ["J", "Q", "K"]:
            return 10
        elif card == "A":
            # Use 11 if it doesn't bust, otherwise use 1
            if current_sum + 11 <= target:
                return 11
            else:
                return 1
        else:
            return int(card)
    
    def calculate_hand_value(hand: list[str], target: int) -> int:
        """Calculate the total value of the hand, optimally handling Aces."""
        total = 0
        aces = 0
        
        # First, add all non-Ace cards
        for card in hand:
            if card == "A":
                aces += 1
            elif card in ["J", "Q", "K"]:
                total += 10
            else:
                total += int(card)
        
        # Handle Aces optimally
        for _ in range(aces):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
        
        return total
    
    def get_remaining_cards(hand: list[str]) -> list[str]:
        """Get the cards remaining in our deck."""
        all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        remaining = []
        hand_set = set(hand)
        
        for card in all_cards:
            if card not in hand_set:
                remaining.append(card)
        
        return remaining
    
    current_value = calculate_hand_value(hand, target)
    
    # If we're already at or very close to target, stay
    if current_value >= target - 1:
        return "STAY"
    
    # Get remaining cards and calculate probabilities
    remaining_cards = get_remaining_cards(hand)
    
    if not remaining_cards:
        return "STAY"
    
    # Calculate expected outcomes for hitting
    bust_count = 0
    safe_outcomes = []
    
    for card in remaining_cards:
        card_val = card_value(card, current_value, target)
        new_total = current_value + card_val
        
        if new_total > target:
            bust_count += 1
        else:
            safe_outcomes.append(new_total)
    
    bust_probability = bust_count / len(remaining_cards)
    
    # Conservative strategy: don't hit if bust probability is too high
    if bust_probability > 0.3:
        return "STAY"
    
    # If we're far from target and bust probability is low, hit
    if current_value <= target - 5 and bust_probability <= 0.2:
        return "HIT"
    
    # For moderate distances, consider expected value
    if safe_outcomes:
        avg_safe_outcome = sum(safe_outcomes) / len(safe_outcomes)
        current_distance = target - current_value
        expected_distance = target - avg_safe_outcome
        
        # Hit if expected outcome is better and bust probability is reasonable
        if expected_distance < current_distance and bust_probability <= 0.25:
            return "HIT"
    
    return "STAY"
