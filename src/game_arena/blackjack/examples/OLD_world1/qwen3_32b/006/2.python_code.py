
from functools import lru_cache

ALL_CARDS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")

def calculate_value(hand_tuple, target):
    total = 0
    aces = 0
    for card in hand_tuple:
        if card == "A":
            total += 11
            aces += 1
        elif card in {"J", "Q", "K"}:
            total += 10
        else:
            total += int(card)
    while total > target and aces > 0:
        total -= 10
        aces -= 1
    return total


@lru_cache(maxsize=None)
def compare_scores_memo(my_score, opponent_score, target):
    if opponent_score > target:
        return 1.0  # I win
    my_dist = abs(my_score - target)
    opp_dist = abs(opponent_score - target)
    if my_dist < opp_dist:
        return 1.0
    elif my_dist > opp_dist:
        return 0.0
    else:
        return 0.5


@lru_cache(maxsize=None)
def best_action_memo(hand_tuple: tuple, target: int):
    current_val = calculate_value(hand_tuple, target)
    if current_val > target:
        return ("BUST", 0.0)

    # Evaluate staying
    stay_score = current_val
    # Opponent starts with empty hand
    opponent_starting_hand = tuple()
    prob_stay_win = opponent_hand_prob_memo(hand_tuple=opponent_starting_hand, target=target, my_score=stay_score)

    # Evaluate hitting
    if len(hand_tuple) == 13:
        return ("STAY", prob_stay_win)

    remaining_cards = [card for card in ALL_CARDS if card not in hand_tuple]
    num_remaining = len(remaining_cards)
    expected_prob_hit = 0.0

    for card in remaining_cards:
        new_hand = list(hand_tuple) + [card]
        new_hand_sorted = tuple(sorted(new_hand))
        _, prob_win = best_action_memo(new_hand_sorted, target)
        expected_prob_hit += prob_win / num_remaining

    if expected_prob_hit > prob_stay_win:
        return ("HIT", expected_prob_hit)
    else:
        return ("STAY", prob_stay_win)


@lru_cache(maxsize=None)
def opponent_hand_prob_memo(hand_tuple: tuple, target: int, my_score: int):
    current_val = calculate_value(hand_tuple, target)
    if current_val > target:
        return 1.0  # Opponent busts, I win

    # Evaluate if opponent stays
    opponent_score = current_val
    stay_outcome = compare_scores_memo(my_score, opponent_score, target)

    # Evaluate if opponent hits
    if len(hand_tuple) == 13:
        return stay_outcome

    remaining_cards = [card for card in ALL_CARDS if card not in hand_tuple]
    num_remaining = len(remaining_cards)
    hit_outcome = 0.0

    for card in remaining_cards:
        new_hand = list(hand_tuple) + [card]
        new_hand_sorted = tuple(sorted(new_hand))
        hit_outcome += opponent_hand_prob_memo(new_hand_sorted, target, my_score) / num_remaining

    return min(stay_outcome, hit_outcome)


def policy(hand: list[str], target: int) -> str:
    hand_tuple = tuple(sorted(hand))
    action, _ = best_action_memo(hand_tuple, target)
    return action
