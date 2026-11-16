
def policy(hand: list[str], target: int) -> str:
    def calculate_hand_value(hand_cards):
        # Separate aces and other cards
        aces = hand_cards.count("A")
        non_aces_total = 0
        
        for card in hand_cards:
            if card == "A":
                continue
            elif card in ["J", "Q", "K"]:
                non_aces_total += 10
            else:
                non_aces_total += int(card)
        
        # Calculate optimal ace values
        hand_value = non_aces_total
        for _ in range(aces):
            if hand_value + 11 <= target:
                hand_value += 11
            else:
                hand_value += 1
        
        return hand_value
    
    current_value = calculate_hand_value(hand)
    
    # If we've reached or exceeded target, must stay
    if current_value >= target:
        return "STAY"
    
    # Simple threshold-based policy
    # Hit if we're at least 5 points away from target
    if target - current_value >= 5:
        return "HIT"
    else:
        return "STAY"
