
def policy(hand: list[str], target: int) -> str:
    def card_value(card: str, current_sum: int, target: int) -> int:
        """Calculate the value of a card given current hand state"""
        if card in ["J", "Q", "K"]:
            return 10
        elif card == "A":
            # Ace is 11 if it doesn't make us exceed target, otherwise 1
            if current_sum + 11 <= target:
                return 11
            else:
                return 1
        else:
            return int(card)
    
    def calculate_hand_value(hand: list[str], target: int) -> int:
        """Calculate total value of hand with optimal Ace handling"""
        # First, calculate with all Aces as 11
        total = 0
        aces = 0
        
        for card in hand:
            if card == "A":
                aces += 1
                total += 11
            elif card in ["J", "Q", "K"]:
                total += 10
            else:
                total += int(card)
        
        # Convert Aces from 11 to 1 if we're over target
        while total > target and aces > 0:
            total -= 10  # Convert an Ace from 11 to 1
            aces -= 1
            
        return total
    
    def get_remaining_cards(hand: list[str]) -> list[str]:
        """Get list of cards still available in deck"""
        all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        remaining = []
        hand_set = set(hand)
        
        for card in all_cards:
            if card not in hand_set:
                remaining.append(card)
        
        return remaining
    
    # Calculate current hand value
    current_value = calculate_hand_value(hand, target)
    
    # If we're already at or very close to target, stay
    if current_value >= target - 1:
        return "STAY"
    
    # Get remaining cards and calculate bust probability
    remaining_cards = get_remaining_cards(hand)
    
    if not remaining_cards:  # No cards left
        return "STAY"
    
    # Count how many remaining cards would bust us
    bust_cards = 0
    safe_cards = 0
    
    for card in remaining_cards:
        card_val = card_value(card, current_value, target)
        if current_value + card_val > target:
            bust_cards += 1
        else:
            safe_cards += 1
    
    bust_probability = bust_cards / len(remaining_cards)
    
    # Conservative strategy: stay if bust probability is too high
    # Adjust threshold based on how far we are from target
    distance_to_target = target - current_value
    
    # If we're very far from target, take more risk
    if distance_to_target >= 8:
        threshold = 0.6
    elif distance_to_target >= 5:
        threshold = 0.4
    elif distance_to_target >= 3:
        threshold = 0.3
    else:
        threshold = 0.2
    
    # Also consider if our current score is very low (risky to stay)
    if current_value <= target * 0.6:  # If we're at 60% or less of target
        threshold = 0.7  # Take more risk
    
    if bust_probability <= threshold:
        return "HIT"
    else:
        return "STAY"
