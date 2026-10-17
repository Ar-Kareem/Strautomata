
def computed_value(hand, target):
    non_ace = 0
    aces = 0
    for card in hand:
        if card == 'A':
            aces += 1
        elif card in ['J', 'Q', 'K']:
            non_ace += 10
        else:
            non_ace += int(card)
    total = non_ace + aces
    for _ in range(aces):
        if total + 10 <= target:
            total += 10
        else:
            break
    return total

def policy(hand, target):
    current_value = computed_value(hand, target)
    if current_value > target:
        return "STAY"
    if current_value == target:
        return "STAY"
    
    all_cards = {'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'}
    remaining_cards = all_cards - set(hand)
    
    if current_value > target - 3:
        safe_cards = []
        for c in remaining_cards:
            new_value = computed_value(hand + [c], target)
            if new_value <= target:
                safe_cards.append(c)
        if not safe_cards:
            return "STAY"
        better_cards = []
        for c in safe_cards:
            new_value = computed_value(hand + [c], target)
            if abs(new_value - target) < abs(current_value - target):
                better_cards.append(c)
        if better_cards:
            return "HIT"
        else:
            return "STAY"
    else:
        return "HIT"
