
import functools

all_cards = frozenset(["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"])

@functools.lru_cache(maxsize=None)
def stay_value(state: frozenset, target: int) -> float:
    num_aces = sum(1 for c in state if c == "A")
    fixed_min = sum(10 if c in {"J", "Q", "K"} else int(c) for c in state if c != "A")
    min_sum = fixed_min + num_aces * 1
    if min_sum > target:
        return -999.0
    max_score = min_sum
    for _ in range(num_aces):
        if max_score + 10 <= target:
            max_score += 10
        else:
            break
    return float(max_score)

@functools.lru_cache(maxsize=None)
def get_value(state: frozenset, target: int) -> float:
    s_val = stay_value(state, target)
    rem = all_cards - state
    if not rem:
        return s_val
    h_val = 0.0
    n = len(rem)
    for c in rem:
        new_state = state | frozenset((c,))
        h_val += get_value(new_state, target)
    h_val /= n
    return max(s_val, h_val)

def policy(hand: list[str], target: int) -> str:
    state = frozenset(hand)
    s_val = stay_value(state, target)
    opt_val = get_value(state, target)
    if opt_val > s_val:
        return "HIT"
    else:
        return "STAY"
