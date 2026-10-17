
def hand_value(hand, target):
    has_ace = 'A' in hand
    base = 0
    for card in hand:
        if card == 'A':
            base += 1
        elif card in ['J', 'Q', 'K']:
            base += 10
        else:
            base += int(card)
    if has_ace:
        soft = base + 10
        if soft <= target:
            return soft
        else:
            return base
    else:
        return base

def policy(hand, target):
    all_cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    current_v = hand_value(hand, target)
    stay_score = current_v if current_v <= target else -100
    remaining = [card for card in all_cards if card not in hand]
    num_remaining = len(remaining)
    if num_remaining == 0:
        return "STAY"
    hit_score_sum = 0
    for card in remaining:
        new_hand = hand + [card]
        new_v = hand_value(new_hand, target)
        hit_score_sum += new_v if new_v <= target else -100
    expected_hit = hit_score_sum / num_remaining
    if expected_hit > stay_score:
        return "HIT"
    else:
        return "STAY"
