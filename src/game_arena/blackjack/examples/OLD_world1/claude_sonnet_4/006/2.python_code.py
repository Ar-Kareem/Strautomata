
def policy(hand: list[str], target: int) -> str:
    def card_value(card, current_sum, target):
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
    
    def calculate_hand_value(hand, target):
        # First pass: count aces and calculate non-ace values
        aces = hand.count("A")
        non_ace_sum = 0
        
        for card in hand:
            if card != "A":
                if card in ["J", "Q", "K"]:
                    non_ace_sum += 10
                else:
                    non_ace_sum += int(card)
        
        # Now handle aces optimally
        total = non_ace_sum
        for _ in range(aces):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
                
        return total
    
    # Calculate current hand value
    current_value = calculate_hand_value(hand, target)
    
    # If we're already at or over target, stay
    if current_value >= target:
        return "STAY"
    
    # Calculate remaining cards in deck
    cards_in_deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining_cards = []
    
    for card in cards_in_deck:
        if card not in hand:
            remaining_cards.append(card)
    
    # If no cards left, must stay
    if not remaining_cards:
        return "STAY"
    
    # Calculate expected value of hitting vs staying
    bust_cards = 0
    total_improvement = 0
    
    for card in remaining_cards:
        new_value = current_value + card_value(card, current_value, target)
        
        if new_value > target:
            bust_cards += 1
        else:
            # Calculate how much closer this gets us to target
            current_distance = target - current_value
            new_distance = target - new_value
            improvement = current_distance - new_distance
            total_improvement += improvement
    
    # Calculate bust probability
    bust_probability = bust_cards / len(remaining_cards)
    
    # Conservative strategy: don't hit if bust probability is too high
    # or if we're already reasonably close to target
    
    # If we're close to target (within 4), be more conservative
    distance_to_target = target - current_value
    
    if distance_to_target <= 2:
        return "STAY"
    elif distance_to_target <= 4 and bust_probability > 0.3:
        return "STAY"
    elif distance_to_target <= 6 and bust_probability > 0.5:
        return "STAY"
    elif bust_probability > 0.6:
        return "STAY"
    else:
        return "HIT"
