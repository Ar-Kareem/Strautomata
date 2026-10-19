
def policy(hand: list[str], target: int) -> str:
    def compute_hand_value(cards, t):
        non_ace_sum = 0
        ace_count = 0
        for card in cards:
            if card == "A":
                ace_count += 1
            elif card in ["J", "Q", "K"]:
                non_ace_sum += 10
            else:
                non_ace_sum += int(card)
        
        # Try using 11 for all Aces
        total_with_11 = non_ace_sum + 11 * ace_count
        if total_with_11 <= t:
            return total_with_11
        else:
            return non_ace_sum + ace_count
    
    current_value = compute_hand_value(hand, target)
    
    # If we exactly reached the target, stay
    if current_value == target:
        return "STAY"
    
    # Get all 13 cards and subtract those in hand
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining = [card for card in all_cards if card not in hand]
    
    # If no cards left, must stay
    if len(remaining) == 0:
        return "STAY"
    
    bust_count = 0
    for card in remaining:
        new_hand = hand + [card]
        new_value = compute_hand_value(new_hand, target)
        if new_value > target:
            bust_count += 1
    
    bust_ratio = bust_count / len(remaining)
    
    # Decision based on how close we are to target
    if current_value >= target - 1:
        # Very close to target
        if bust_count == 0:
            return "HIT"
        else:
            return "STAY"
    elif current_value >= target - 3:
        # Close to target
        if bust_ratio < 0.2:
            return "HIT"
        else:
            return "STAY"
    else:
        # Not close to target
        if bust_ratio < 0.35:
            return "HIT"
        else:
            return "STAY"
