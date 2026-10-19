
def policy(hand: list[str], target: int) -> str:
    # All possible cards in a suit
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    
    def calculate_hand_value(cards):
        """Calculate the best possible value of a hand with proper Ace handling"""
        # First count non-Ace cards
        value = 0
        ace_count = 0
        
        for card in cards:
            if card == "A":
                ace_count += 1
            elif card in ["J", "Q", "K"]:
                value += 10
            else:  # 2-10
                value += int(card)
        
        # Handle aces optimally - try 11 first, fall back to 1 if needed
        for _ in range(ace_count):
            if value + 11 <= target:
                value += 11
            else:
                value += 1
                
        return value
    
    # Calculate current hand value
    current_value = calculate_hand_value(hand)
    
    # If we've already reached or exceeded target, stay
    if current_value >= target:
        return "STAY"
    
    # Calculate how many cards we've drawn
    cards_drawn = len(hand)
    
    # Cards we haven't drawn yet
    drawn_cards = set(hand)
    remaining_cards = [card for card in all_cards if card not in drawn_cards]
    
    # If no cards left to draw, we must stay
    if not remaining_cards:
        return "STAY"
    
    # Calculate the gap to target
    gap = target - current_value
    
    # Simple strategy based on gap and risk
    # If gap is small, be more conservative
    if gap <= 3:
        # Very close to target, be conservative
        # Only hit if there's very low risk of busting
        safe_cards = 0
        for card in remaining_cards:
            if card == "A":
                card_value = 1  # Conservative estimate
            elif card in ["J", "Q", "K"]:
                card_value = 10
            else:
                card_value = int(card)
            
            # Check if this card would bust us
            if card_value <= gap:
                safe_cards += 1
        
        # If less than 30% of remaining cards are safe, stay
        if safe_cards / len(remaining_cards) < 0.3:
            return "STAY"
        else:
            return "HIT"
    elif gap <= 7:
        # Moderately close, calculate some risk
        safe_cards = 0
        for card in remaining_cards:
            if card == "A":
                card_value = 1  # Conservative
            elif card in ["J", "Q", "K"]:
                card_value = 10
            else:
                card_value = int(card)
            
            if card_value <= gap:
                safe_cards += 1
        
        # If less than 50% of cards are safe, stay
        if safe_cards / len(remaining_cards) < 0.5:
            return "STAY"
        else:
            return "HIT"
    else:
        # Far from target, be more aggressive
        # But still check if there are any really dangerous cards
        very_dangerous = 0
        for card in remaining_cards:
            if card == "A":
                card_value = 11  # If we're far, we can probably handle an 11
            elif card in ["J", "Q", "K"]:
                card_value = 10
            else:
                card_value = int(card)
            
            # Check if this card would be very dangerous (close to busting)
            if current_value + card_value > target:
                very_dangerous += 1
        
        # If more than 80% of cards are very dangerous, stay
        if very_dangerous / len(remaining_cards) > 0.8:
            return "STAY"
        else:
            return "HIT"
