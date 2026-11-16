
def policy(hand: list[str], target: int) -> str:
    def card_value(card, current_total, target):
        """Calculate the value of a card given current hand total and target"""
        if card in ["J", "Q", "K"]:
            return 10
        elif card == "A":
            # Ace is 11 if it keeps us at or below target, otherwise 1
            if current_total + 11 <= target:
                return 11
            else:
                return 1
        else:
            return int(card)
    
    def calculate_hand_value(hand, target):
        """Calculate total hand value with proper Ace handling"""
        # First pass: count aces as 11, others at face value
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
        
        # Convert aces from 11 to 1 as needed to stay under target if possible
        while total > target and aces > 0:
            total -= 10  # Convert an ace from 11 to 1
            aces -= 1
            
        return total
    
    # Calculate current hand value
    current_value = calculate_hand_value(hand, target)
    
    # If we're already at or over target, we must stay
    if current_value >= target:
        return "STAY"
    
    # Determine which cards we've already used
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining_cards = []
    used_cards = set(hand)
    
    for card in all_cards:
        if card not in used_cards:
            remaining_cards.append(card)
    
    if not remaining_cards:  # No cards left
        return "STAY"
    
    # Calculate how many remaining cards would bust us
    bust_cards = 0
    safe_cards = 0
    
    for card in remaining_cards:
        card_val = card_value(card, current_value, target)
        if current_value + card_val > target:
            bust_cards += 1
        else:
            safe_cards += 1
    
    total_remaining = len(remaining_cards)
    bust_probability = bust_cards / total_remaining if total_remaining > 0 else 1.0
    
    # Decision logic based on current value relative to target and bust probability
    distance_to_target = target - current_value
    
    # If we're very close to target, be more conservative
    if distance_to_target <= 2:
        if bust_probability > 0.3:  # 30% bust chance is too risky when close
            return "STAY"
    elif distance_to_target <= 4:
        if bust_probability > 0.5:  # 50% bust chance when moderately close
            return "STAY"
    else:
        if bust_probability > 0.7:  # 70% bust chance when far from target
            return "STAY"
    
    # Additional consideration: if we're in a decent position, don't risk it
    target_percentage = current_value / target
    if target_percentage >= 0.85 and bust_probability > 0.4:
        return "STAY"
    
    return "HIT"
