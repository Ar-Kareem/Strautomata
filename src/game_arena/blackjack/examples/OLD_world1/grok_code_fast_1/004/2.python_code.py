
def get_value(hand, target):
    value = 0
    aces = 0
    for card in hand:
        if card == "A":
            aces += 1
            value += 11
        elif card in ["J", "Q", "K"]:
            value += 10
        else:
            value += int(card)
    while value > target and aces > 0:
        value -= 10
        aces -= 1
    return value

def policy(hand, target):
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining = [c for c in all_cards if c not in hand]
    if not remaining:
        return "STAY"
    v = get_value(hand, target)
    expected_hit = 0.0
    for card in remaining:
        new_hand = hand + [card]
        new_v = get_value(new_hand, target)
        score = new_v if new_v <= target else -9999
        expected_hit += score
    expected_hit /= len(remaining)
    if v > expected_hit:
        return "STAY"
    else:
        return "HIT"
