
def policy(hand: list[str], target: int) -> str:
    def calculate_hand_value(cards, t):
        value = 0
        aces = 0
        for card in cards:
            if card in {'J', 'Q', 'K'}:
                value += 10
            elif card == 'A':
                aces += 1
            else:
                value += int(card)
        for _ in range(aces):
            if value + 11 <= t:
                value += 11
            else:
                value += 1
        return value
    
    current_value = calculate_hand_value(hand, target)
    if current_value >= target:
        return "STAY"
    
    all_cards = {'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'}
    remaining = all_cards - set(hand)
    
    current_diff = target - current_value
    for card in remaining:
        temp_hand = hand + [card]
        temp_value = calculate_hand_value(temp_hand, target)
        if temp_value > target:
            continue
        temp_diff = target - temp_value
        if temp_diff < current_diff:
            return "HIT"
    
    return "STAY"
