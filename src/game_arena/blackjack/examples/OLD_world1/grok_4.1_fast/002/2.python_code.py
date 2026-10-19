
import functools

ALL_CARDS = frozenset(['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'])

def policy(hand: list[str], target: int) -> str:
    def compute_min_score(hand_list: list[str]) -> int:
        non_ace = 0
        aces_count = 0
        for card in hand_list:
            if card == 'A':
                aces_count += 1
            elif card in ('J', 'Q', 'K'):
                non_ace += 10
            else:
                non_ace += int(card)
        return non_ace + aces_count

    def compute_max_score(hand_list: list[str], tgt: int) -> int:
        non_ace = 0
        aces_count = 0
        for card in hand_list:
            if card == 'A':
                aces_count += 1
            elif card in ('J', 'Q', 'K'):
                non_ace += 10
            else:
                non_ace += int(card)
        score = non_ace + aces_count
        for _ in range(aces_count):
            if score + 10 <= tgt:
                score += 10
            else:
                break
        return score

    current_set = frozenset(hand)
    curr_score = compute_max_score(hand, target)
    remaining_set = ALL_CARDS - current_set
    num_remaining = len(remaining_set)
    if num_remaining == 0:
        return "STAY"

    @functools.lru_cache(maxsize=None)
    def get_expected_value(state: frozenset) -> float:
        curr_s = compute_max_score(list(state), target)
        rem = ALL_CARDS - state
        r = len(rem)
        if r == 0:
            return float(curr_s)
        stay_val = float(curr_s)
        hit_val = 0.0
        BUST_VAL = -1.0
        for next_c in rem:
            new_state = state.union([next_c])
            new_list = list(new_state)
            min_s = compute_min_score(new_list)
            if min_s > target:
                contrib = BUST_VAL
            else:
                contrib = get_expected_value(new_state)
            hit_val += contrib / r
        return max(stay_val, hit_val)

    # Compute hit_val for current state
    hit_val = 0.0
    BUST_VAL = -1.0
    for next_c in remaining_set:
        new_set = current_set.union([next_c])
        new_list = list(new_set)
        min_s = compute_min_score(new_list)
        if min_s > target:
            contrib = BUST_VAL
        else:
            contrib = get_expected_value(new_set)
        hit_val += contrib / num_remaining

    stay_val = float(curr_score)
    if hit_val > stay_val:
        return "HIT"
    return "STAY"
