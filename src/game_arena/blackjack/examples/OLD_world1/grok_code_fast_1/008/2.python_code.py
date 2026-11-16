
def value(hand: list[str], target: int) -> int:
    sum_val = 0
    aces = 0
    for card in hand:
        if card == 'A':
            sum_val += 11
            aces += 1
        elif card in ['J', 'Q', 'K']:
            sum_val += 10
        else:
            sum_val += int(card)
    while sum_val > target and aces > 0:
        sum_val -= 10
        aces -= 1
    return sum_val

def policy(hand: list[str], target: int) -> str:
    if not hand:
        current_sum = 0
    else:
        current_sum = value(hand, target)
    
    if current_sum > target:
        return "STAY"  # Though ideally, this shouldn't be called if already busted
    
    remaining = 13 - len(hand)
    if remaining > 3:
        margin = 5
    else:
        margin = 2
    
    if current_sum >= target - margin:
        return "STAY"
    else:
        return "HIT"
