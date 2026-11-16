
def policy(hand, target):
    def compute_hand_value(hand, target):
        nonA = 0
        aces = 0
        for card in hand:
            if card == 'A':
                aces += 1
            elif card in ['J', 'Q', 'K']:
                nonA += 10
            else:
                nonA += int(card)
        total0 = nonA + aces * 11
        if total0 <= target:
            return total0
        else:
            k = min(aces, (total0 - target + 9) // 10)
            return total0 - 10 * k

    H = compute_hand_value(hand, target)
    if H > target:
        return "STAY"
    if target <= 15:
        if H >= target - 1:
            return "STAY"
        else:
            return "HIT"
    else:
        if H >= target - 2:
            return "STAY"
        else:
            return "HIT"
