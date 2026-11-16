
def policy(hand: list[str], target: int) -> str:
    # Calculate current hand value with optimal ace handling
    def calculate_hand_value(hand_cards):
        # Count aces and sum other cards
        aces_count = 0
        total = 0
        
        for card in hand_cards:
            if card == "A":
                aces_count += 1
            elif card in ["J", "Q", "K"]:
                total += 10
            else:  # 2-10
                total += int(card)
        
        # Add aces as 11 if possible, otherwise as 1
        for _ in range(aces_count):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
        
        return total
    
    current_value = calculate_hand_value(hand)
    
    # If we've already busted or reached/beat target, stay
    if current_value >= target:
        return "STAY"
    
    # If we're close to target, play conservatively
    # Threshold of 3: if we're within 3 points of target, stay
    if target - current_value <= 3:
        return "STAY"
    
    # Otherwise, try to improve our hand
    return "HIT"
