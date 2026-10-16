
def policy(hand: list[str], target: int) -> str:
    def hand_value(cards, target):
        """Calculate the value of a hand given the target."""
        value = 0
        num_aces = 0
        
        for card in cards:
            if card == "A":
                num_aces += 1
                value += 11
            elif card in ["J", "Q", "K"]:
                value += 10
            else:
                value += int(card)
        
        # Convert aces from 11 to 1 if we're over target
        while value > target and num_aces > 0:
            value -= 10
            num_aces -= 1
        
        return value
    
    # Calculate current hand value
    current = hand_value(hand, target)
    
    # If we're at or over target, we must stay
    if current >= target:
        return "STAY"
    
    # Determine which cards remain in our deck
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining = [c for c in all_cards if c not in hand]
    
    # If no cards remain, must stay
    if not remaining:
        return "STAY"
    
    # Analyze outcomes of drawing each possible next card
    safe_cards = 0
    safe_values_sum = 0
    
    for card in remaining:
        next_hand = hand + [card]
        next_value = hand_value(next_hand, target)
        if next_value <= target:
            safe_cards += 1
            safe_values_sum += next_value
    
    # If all remaining cards would bust us, stay
    if safe_cards == 0:
        return "STAY"
    
    bust_probability = 1 - (safe_cards / len(remaining))
    avg_safe_value = safe_values_sum / safe_cards
    
    # Strategic decision making
    # 1. If very close to target, stay (conservative near target)
    if current >= target - 3:
        return "STAY"
    
    # 2. If high bust probability, stay
    if bust_probability > 0.5:
        return "STAY"
    
    # 3. If far from target and low bust risk, hit
    if current <= target - 7 and bust_probability < 0.3:
        return "HIT"
    
    # 4. Medium range: hit if more safe cards than bust cards
    if safe_cards >= len(remaining) / 2:
        return "HIT"
    else:
        return "STAY"
