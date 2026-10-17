
def policy(hand: list[str], target: int) -> str:
    # Calculate current hand value
    def hand_value(hand):
        total = 0
        aces = 0
        
        for card in hand:
            if card in ["J", "Q", "K"]:
                total += 10
            elif card == "A":
                aces += 1
            else:
                total += int(card)
        
        # Add aces optimally
        for _ in range(aces):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
                
        return total
    
    current_value = hand_value(hand)
    
    # If we've already busted, it's too late (but we shouldn't be called in this case)
    if current_value > target:
        return "STAY"
    
    # If we're at or above a safe threshold, stay
    if current_value >= target - 3:
        return "STAY"
    
    # Calculate remaining cards in our deck
    full_deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining_cards = [card for card in full_deck if card not in hand]
    
    # If no cards remain, we must stay
    if not remaining_cards:
        return "STAY"
    
    # Calculate potential outcomes of hitting
    safe_hits = 0
    total_hits = 0
    
    for card in remaining_cards:
        # Create a new hand with this card
        new_hand = hand + [card]
        new_value = hand_value(new_hand)
        total_hits += 1
        
        # Check if this hit would be safe
        if new_value <= target:
            safe_hits += 1
    
    # If all remaining cards would cause us to bust, stay
    if safe_hits == 0:
        return "STAY"
    
    # Calculate probability of staying safe if we hit
    safety_prob = safe_hits / total_hits
    
    # If we have a high chance of staying safe, hit
    # But be more cautious as we get closer to the target
    threshold = 0.5 + (current_value / target) * 0.3
    
    if safety_prob >= threshold:
        return "HIT"
    else:
        return "STAY"
