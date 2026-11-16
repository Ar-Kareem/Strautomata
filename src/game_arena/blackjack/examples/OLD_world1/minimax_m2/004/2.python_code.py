
def hand_value(hand, T):
    base_value = 0
    ace_count = 0
    for card in hand:
        if card == 'A':
            ace_count += 1
        elif card in ['J', 'Q', 'K']:
            base_value += 10
        else:
            base_value += int(card)
    
    candidate_value = base_value + 11 * ace_count
    if candidate_value <= T:
        return candidate_value
    else:
        return base_value + ace_count

def policy(hand, target):
    current_value = hand_value(hand, target)
    
    if current_value >= target - 1:
        return "STAY"
    
    all_ranks = {'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'}
    remaining = all_ranks - set(hand)
    
    if len(remaining) == 0:
        return "STAY"
    
    non_bust_count = 0
    for card in remaining:
        new_hand = hand + [card]
        new_value = hand_value(new_hand, target)
        if new_value <= target:
            non_bust_count += 1
    
    threshold = len(remaining) // 2 + 1
    if non_bust_count >= threshold:
        return "HIT"
    else:
        return "STAY"
