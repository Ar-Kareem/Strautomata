
from functools import lru_cache
from typing import List

def compute_sum(hand: List[str], target: int) -> int:
    sum_non_ace = 0
    aces_count = 0
    for card in hand:
        if card == 'A':
            aces_count += 1
        else:
            sum_non_ace += 10 if card in {'J', 'Q', 'K'} else int(card)
    
    sum_initial = sum_non_ace + 11 * aces_count
    if sum_initial <= target:
        return sum_initial
    else:
        return sum_non_ace + aces_count

@lru_cache(maxsize=None)
def prob_win(hand: frozenset, target: int) -> float:
    hand_sum = compute_sum(list(hand), target) if hand else 0
    if hand_sum > target:
        return 0.0
    
    remaining_deck = frozenset({
        '2', '3', '4', '5', '6', '7', '8', '9', '10',
        'J', 'Q', 'K', 'A'
    } - hand)
    
    if not remaining_deck:
        remaining_opponent_deck = frozenset({
            '2', '3', '4', '5', '6', '7', '8', '9', '10',
            'J', 'Q', 'K', 'A'
        })
        sum_opponent = compute_sum(list(remaining_opponent_deck), target)
        prob_opponent_sum = 1 if sum_opponent > target else 0
        if sum_opponent > target:
            return 1.0
        return 0.5 if sum_opponent == list(to_stay_sum - hand_sum) == 0 else 0.0
    
    # Stay Probability
    sum_stay = hand_sum
    deck_after_stay = frozenset({
        '2', '3', '4', '5', '6', '7', '8', '9', '10',
        'J', 'Q', 'K', 'A'
    } - hand)
    prob_opponent_sum_less = 0.0
    draw_prob = 1 / len(deck_after_stay)
    for card in deck_after_stay:
        opp_hand = frozenset([card]) if card not in deck_after_stay else frozenset()
        opp_sum = compute_sum(list(opp_hand), target)
        if opp_sum > target:
            prob_opponent_sum_less += 1
        elif opp_sum < sum_stay:
            prob_opponent_sum_less += 1
        else:
            prob_opponent_sum_less += 0.5
    p_stay = prob_opponent_sum_less / len(deck_after_stay)
    
    # Hit Probability
    p_hit = 0.0
    for card in remaining_deck:
        new_hand = frozenset(hand | {card})
        new_sum = compute_sum(list(new_hand), target)
        if new_sum > target:
            prob = 0.0  # Bust
        else:
            prob = prob_win(new_hand, target)
        p_hit += (prob * draw_prob) / len(remaining_deck)
    
    return max(p_stay, p_hit)

def policy(hand: List[str], target: int) -> str:
    hand_set = frozenset(hand)
    current_sum = compute_sum(hand, target)
    if current_sum > target:
        return "STAY"
    
    remaining_deck = frozenset({
        '2', '3', '4', '5', '6', '7', '8', '9', '10',
        'J', 'Q', 'K', 'A'
    } - hand_set)
    
    if not remaining_deck:
        return "STAY"
    
    draw_prob = 1.0 / len(remaining_deck)
    expected_value_hit = 0.0
    for card in remaining_deck:
        new_hand = frozenset(hand_set | {card})
        new_sum = compute_sum(list(new_hand), target)
        if new_sum > target:
            expected_value_hit += 0.0 * draw_prob
            continue
        expected_value_hit += prob_win(new_hand, target) * draw_prob
    
    current_hand_value = compute_sum(hand, target)
    opponent_win_prob = 0.0
    for card in remaining_deck:
        opp_hand = frozenset(hand_set | {card})
        opp_sum = compute_sum(list(opp_hand), target)
        if opp_sum > target:
            opponent_win_prob += 0.0
        elif opp_sum < current_hand_value:
            opponent_win_prob += 1.0
        else:
            opponent_win_prob += 0.5
    opponent_win_prob /= len(remaining_deck)
    p_stay = 1 - opponent_win_prob
    p_stay += 0.5 / len(remaining_deck)
    
    return "HIT" if expected_value_hit > p_stay else "STAY"