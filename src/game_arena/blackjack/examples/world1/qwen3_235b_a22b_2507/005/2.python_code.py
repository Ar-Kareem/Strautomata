
def policy(hand: list[str], target: int) -> str:
    # Define the value of non-Ace cards
    value_map = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10}
    
    def calculate_value(current_hand, t):
        non_aces = [c for c in current_hand if c != 'A']
        num_aces = len(current_hand) - len(non_aces)
        non_ace_sum = sum(value_map[c] for c in non_aces)
        total = non_ace_sum + num_aces  # Aces count as 1 initially
        # Upgrade Aces from 1 to 11 (add 10) if it doesn't exceed target
        for _ in range(num_aces):
            if total + 10 <= t:
                total += 10
            else:
                break
        return total

    # Calculate current hand value
    current_value = calculate_value(hand, target)
    
    # If already at or above target, stay (bust or perfect)
    if current_value > target:
        return "STAY"
    if current_value == target:
        return "STAY"
    if current_value >= target - 2:
        return "STAY"
    if current_value >= 19:
        return "STAY"
    
    # Determine remaining cards in the deck
    all_cards = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
    remaining = [c for c in all_cards if c not in hand]
    n_remaining = len(remaining)
    
    # If no cards left, must stay
    if n_remaining == 0:
        return "STAY"
    
    # Simulate drawing each remaining card to see if it causes a bust
    bust_count = 0
    for card in remaining:
        new_hand = hand + [card]
        new_value = calculate_value(new_hand, target)
        if new_value > target:
            bust_count += 1
    
    bust_prob = bust_count / n_remaining
    
    # If more than 50% chance of busting, stay; otherwise, hit
    if bust_prob > 0.5:
        return "STAY"
    else:
        return "HIT"
