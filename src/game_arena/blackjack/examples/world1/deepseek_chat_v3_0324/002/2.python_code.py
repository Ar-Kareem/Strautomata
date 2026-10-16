
def policy(hand: list[str], target: int) -> str:
    # All possible cards in the deck
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    
    # Determine which cards are still available in our deck
    remaining_cards = [card for card in all_cards if card not in hand]
    
    # Calculate current hand value with optimal Ace usage
    def calculate_hand_value(cards):
        value = 0
        aces = 0
        for card in cards:
            if card == "A":
                value += 11
                aces += 1
            elif card in ["J", "Q", "K"]:
                value += 10
            else:  # Number cards
                value += int(card)
        
        # Adjust for Aces if needed
        while value > target and aces > 0:
            value -= 10  # Change Ace from 11 to 1
            aces -= 1
        
        return value
    
    current_value = calculate_hand_value(hand)
    
    # If we're already at or above target, STAY
    if current_value >= target:
        return "STAY"
    
    # Calculate how many remaining cards would keep us at or below target if we HIT
    safe_cards = 0
    total_remaining = len(remaining_cards)
    
    for card in remaining_cards:
        # Calculate new hand value if we drew this card
        new_hand = hand + [card]
        new_value = calculate_hand_value(new_hand)
        
        if new_value <= target:
            safe_cards += 1
    
    # If there are no remaining cards (shouldn't happen as per game rules), STAY
    if total_remaining == 0:
        return "STAY"
    
    # Calculate the probability that a HIT would keep us at or below target
    safe_probability = safe_cards / total_remaining
    
    # Decide based on the probability and current hand value
    if current_value < target - 10:
        # Very far below target - always HIT
        return "HIT"
    elif safe_probability > 0.5:
        # More than half of remaining cards are safe - HIT
        return "HIT"
    else:
        # Less than half of remaining cards are safe - STAY
        return "STAY"
