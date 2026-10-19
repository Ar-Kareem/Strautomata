
def get_sum(hand, T):
    non_aces = 0
    aces = 0
    for c in hand:
        if c == 'A':
            aces += 1
        else:
            v = 10 if c in 'JQK' else int(c)
            non_aces += v
    sum_ac = 11 * aces
    while sum_ac > 0 and non_aces + sum_ac > T:
        sum_ac -= 10
    total = non_aces + sum_ac
    return total if total <= T else 1000  # bust

def policy(hand: list[str], target: int) -> str:
    if not hand:
        return "HIT"
    all_ranks = {'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'}
    drawn = set(hand)
    remaining = all_ranks - drawn
    rem_list = list(remaining)
    curr_sum = get_sum(hand, target)
    score_stay = abs(target - curr_sum) if curr_sum <= target else 1000
    total_score_hit = 0
    for card in rem_list:
        new_hand = hand + [card]
        new_sum = get_sum(new_hand, target)
        dist = abs(target - new_sum) if new_sum <= target else 1000
        total_score_hit += dist
    avg_score_hit = total_score_hit / len(rem_list) if rem_list else 1000
    if avg_score_hit < score_stay:
        return "HIT"
    else:
        return "STAY"
