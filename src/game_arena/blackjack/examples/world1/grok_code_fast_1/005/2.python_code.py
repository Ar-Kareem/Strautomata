
def get_hand_value(hand, target):
    non_A_sum = 0
    num_A = 0
    for card in hand:
        if card == 'A':
            num_A += 1
        else:
            non_A_sum += int(card) if card.isdigit() else 10
    soft = non_A_sum + 11 * num_A
    if soft <= target:
        return soft
    else:
        return non_A_sum + 1 * num_A

def policy(hand, target):
    current = get_hand_value(hand, target)
    if current >= target or current >= target - 5:
        return "STAY"
    else:
        return "HIT"
