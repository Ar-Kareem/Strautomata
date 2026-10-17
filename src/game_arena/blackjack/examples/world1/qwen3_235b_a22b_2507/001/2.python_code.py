
def policy(hand: list[str], target: int) -> str:
    # Define card values
    def card_value(card, current_sum):
        if card in ["J", "Q", "K"]:
            return 10
        elif card == "A":
            # Ace is 11 if it doesn't make us bust, else 1
            if current_sum + 11 <= target:
                return 11
            else:
                return 1
        else:
            return int(card)
    
    # Compute current hand value with optimal Ace handling
    def hand_value(hand, target):
        total = 0
        aces = 0
        for card in hand:
            if card == "A":
                aces += 1
            else:
                total += card_value(card, 0)  # safe value without Ace logic
        # Add Aces with smart logic
        for _ in range(aces):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
        return total
    
    # If no cards yet, definitely hit
    if len(hand) == 0:
        return "HIT"
    
    # Get current value
    current_value = hand_value(hand, target)
    
    # If we're at or over target, stay to avoid busting
    if current_value >= target:
        return "STAY"
    
    # Determine remaining cards
    all_cards = {"A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"}
    hand_set = set(hand)
    remaining_cards = all_cards - hand_set
    
    # If no cards left, we have to stay
    if not remaining_cards:
        return "STAY"
    
    # Simulate hitting: how many remaining cards would cause a bust?
    bust_count = 0
    for card in remaining_cards:
        # Assume we draw this card
        if card == "A":
            # Ace value depends
            if current_value + 11 <= target:
                new_value = current_value + 11
            else:
                new_value = current_value + 1
        else:
            new_value = current_value + card_value(card, 0)
        
        if new_value > target:
            bust_count += 1
    
    bust_probability = bust_count / len(remaining_cards)
    
    # Decision logic
    gap = target - current_value
    
    # If very close to target, stay
    if gap <= 3:
        return "STAY"
    
    # If gap is large and risk is low, hit
    if gap > 3 and bust_probability < 0.5:
        return "HIT"
    
    # Otherwise, play safe
    return "STAY"
