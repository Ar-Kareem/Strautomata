
def policy(hand: list[str], target: int) -> str:
    def card_value(card: str, current_sum: int, target: int) -> int:
        """Calculate the value of a card given current hand sum and target."""
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
    
    def calculate_hand_value(hand: list[str], target: int) -> int:
        """Calculate the total value of the hand, optimally using Aces."""
        total = 0
        aces = []
        
        # First pass: add non-aces and collect aces
        for card in hand:
            if card == "A":
                aces.append(card)
            elif card in ["J", "Q", "K"]:
                total += 10
            else:
                total += int(card)
        
        # Second pass: add aces optimally
        for ace in aces:
            if total + 11 <= target:
                total += 11
            else:
                total += 1
                
        return total
    
    def get_remaining_cards(hand: list[str]) -> list[str]:
        """Get the cards remaining in our deck."""
        all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        remaining = []
        hand_counts = {}
        
        # Count cards in hand
        for card in hand:
            hand_counts[card] = hand_counts.get(card, 0) + 1
        
        # Add remaining cards
        for card in all_cards:
            if hand_counts.get(card, 0) == 0:
                remaining.append(card)
        
        return remaining
    
    current_value = calculate_hand_value(hand, target)
    
    # If we're already at or past target, stay
    if current_value >= target:
        return "STAY"
    
    remaining_cards = get_remaining_cards(hand)
    
    if not remaining_cards:
        return "STAY"
    
    # Calculate probability of busting and expected value after hitting
    bust_count = 0
    total_outcomes = len(remaining_cards)
    sum_if_not_bust = 0
    non_bust_count = 0
    
    for card in remaining_cards:
        new_value = current_value + card_value(card, current_value, target)
        if new_value > target:
            bust_count += 1
        else:
            sum_if_not_bust += new_value
            non_bust_count += 1
    
    bust_probability = bust_count / total_outcomes
    
    # Conservative strategy: don't hit if bust probability is too high
    # Adjust threshold based on how far we are from target
    distance_from_target = target - current_value
    
    # Dynamic threshold: be more aggressive when far from target
    if distance_from_target >= 10:
        max_bust_prob = 0.4
    elif distance_from_target >= 7:
        max_bust_prob = 0.3
    elif distance_from_target >= 5:
        max_bust_prob = 0.25
    else:
        max_bust_prob = 0.2
    
    # Also consider if we're likely to get closer to target
    if non_bust_count > 0:
        avg_value_if_not_bust = sum_if_not_bust / non_bust_count
        improvement = avg_value_if_not_bust - current_value
        
        # If we're very close to target and improvement is small, be more conservative
        if current_value >= target - 3 and improvement < 2:
            max_bust_prob = 0.15
    
    if bust_probability <= max_bust_prob:
        return "HIT"
    else:
        return "STAY"
