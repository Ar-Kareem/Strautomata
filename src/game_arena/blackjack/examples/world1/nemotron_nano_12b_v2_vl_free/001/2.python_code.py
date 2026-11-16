
import math
import functools

CARD_VALUES = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 
               '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}

def calculate_sum(hand, target):
    sum_non_ace = 0
    num_aces = 0
    for card in hand:
        if card == 'A':
            num_aces += 1
        else:
            sum_non_ace += CARD_VALUES[card]
    sum_initial = sum_non_ace + 11 * num_aces
    if sum_initial <= target:
        return sum_initial
    required_reduction = sum_initial - target
    k = math.ceil(required_reduction / 10)
    k = min(k, num_aces)
    k = max(k, 0)
    return sum_initial - 10 * k

def evaluate_player(hand_tuple, target):
    if sum(CARD_VALUES[c] if c != 'A' else 11 for c in hand_tuple) > target:
        return 0.0
    return 1.0

@functools.lru_cache(maxsize=None)
def prob_win(hand, remaining, target, is_user):
    hand = tuple(hand)
    if len(hand) >= len(remaining) + len(hand) - (13 - len(remaining)):
        sum_hand = calculate_sum(hand, target)
        if evaluate_player(hand, target) < 0.5:
            return 0.0
        else:
            return 1.0
    if is_user:
        action_options = ['HIT', 'STAY']
    else:
        action_options = ['HIT', 'STAY']
    
    best_prob = -1.0
    for action in action_options:
        if action == 'STAY':
            opp_hand = ()
            opp_sum = calculate_sum(opp_hand, target)
            if opp_sum > target:
                win_prob = 1.0
            else:
                opp_hand_score = calculate_sum(opp_hand, target)
                my_sum = calculate_sum(hand, target)
                if my_sum > target:
                    win_prob = 0.0
                else:
                    my_distance = target - my_sum
                    opp_distance = target - opp_hand_score
                    if my_distance < opp_distance:
                        win_prob = 1.0
                    elif my_distance == opp_distance:
                        win_prob = 0.5
                    else:
                        win_prob = 0.0
        else:
            total = 0.0
            for card in remaining:
                new_hand = list(hand) + [card]
                new_hand_tuple = tuple(new_hand)
                total += prob_win(new_hand_tuple, remaining - {card}, target, not is_user)
            prob = total / len(remaining)
        win_prob = prob
    return max(win_prob, 0.0)

def policy(hand, target):
    hand_tuple = tuple(hand)
    current_sum = calculate_sum(hand_tuple, target)
    if current_sum > target:
        return 'STAY'
    opponent_card_pool = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
    for card in opponent_card_pool:
        if card not in hand_tuple:
            break
    remaining = [c for c in opponent_card_pool if c not in hand_tuple]
    if len(hand) < 12:
        worse = 0.0
        better = 0.0
        for c in remaining:
            new_hand = list(hand) + [c]
            new_sum = calculate_sum(new_hand, target)
            if new_sum > target:
                worse += 1
            if new_sum < current_sum and new_sum <= target:
                better += 1
        hit_ratio = better / len(remaining) if remaining else 0
        stay_ratio = (current_sum * 10) / target
        return 'HIT' if hit_ratio > stay_ratio else 'STAY'
    return 'STAY'
