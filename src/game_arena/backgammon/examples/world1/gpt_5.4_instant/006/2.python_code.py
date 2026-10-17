
from typing import List, Tuple, Dict
from copy import deepcopy

# ----------------------------
# Backgammon policy
# ----------------------------

def policy(state: dict) -> str:
    moves = enumerate_legal_moves(state)
    if not moves:
        return "H:P,P"
    best_move = None
    best_score = None
    for move_str, new_state in moves:
        score = evaluate_state(new_state)
        if best_score is None or score > best_score:
            best_score = score
            best_move = move_str
    return best_move if best_move is not None else "H:P,P"


# ----------------------------
# Move generation
# ----------------------------

def enumerate_legal_moves(state: Dict) -> List[Tuple[str, Dict]]:
    dice = list(state.get("dice", []))
    if len(dice) == 0:
        return [("H:P,P", deepcopy(state))]

    if len(dice) == 1:
        d = dice[0]
        res = []
        order = "H"
        for src in legal_single_sources(state, d):
            st2 = deepcopy(state)
            apply_move(st2, src, d)
            move_str = f"{order}:{src_token(src)},P"
            res.append((move_str, st2))
        if not res:
            return [("H:P,P", deepcopy(state))]
        return res

    d1, d2 = dice[0], dice[1]
    hi = max(d1, d2)
    lo = min(d1, d2)

    all_candidates = []

    # Order H: high die first, then low die
    all_candidates.extend(generate_for_order(state, first_die=hi, second_die=lo, order_char="H"))

    # Order L: low die first, then high die
    all_candidates.extend(generate_for_order(state, first_die=lo, second_die=hi, order_char="L"))

    # Deduplicate identical move strings; keep best resulting state arbitrary
    uniq = {}
    for m, st in all_candidates:
        if m not in uniq:
            uniq[m] = st
    all_candidates = list(uniq.items())

    if all_candidates:
        return all_candidates

    # If no 2-die plays, must play one die if possible; if only one die can be played, higher die if possible.
    hi_sources = legal_single_sources(state, hi)
    lo_sources = legal_single_sources(state, lo)

    single_res = []
    if hi_sources:
        for src in hi_sources:
            st2 = deepcopy(state)
            apply_move(st2, src, hi)
            single_res.append((f"H:{src_token(src)},P", st2))
        return single_res
    if lo_sources:
        for src in lo_sources:
            st2 = deepcopy(state)
            apply_move(st2, src, lo)
            single_res.append((f"L:{src_token(src)},P", st2))
        return single_res

    return [("H:P,P", deepcopy(state))]


def generate_for_order(state: Dict, first_die: int, second_die: int, order_char: str) -> List[Tuple[str, Dict]]:
    results = []
    first_sources = legal_single_sources(state, first_die)
    for src1 in first_sources:
        st1 = deepcopy(state)
        apply_move(st1, src1, first_die)
        second_sources = legal_single_sources(st1, second_die)
        for src2 in second_sources:
            st2 = deepcopy(st1)
            apply_move(st2, src2, second_die)
            move_str = f"{order_char}:{src_token(src1)},{src_token(src2)}"
            results.append((move_str, st2))
    return results


def legal_single_sources(state: Dict, die: int) -> List:
    # If on bar, only bar moves allowed
    if state["my_bar"] > 0:
        if can_enter_from_bar(state, die):
            return ["B"]
        return []

    srcs = []
    for i in range(24):
        if state["my_pts"][i] <= 0:
            continue
        if is_legal_from_point(state, i, die):
            srcs.append(i)
    return srcs


def can_enter_from_bar(state: Dict, die: int) -> bool:
    dest = 24 - die
    return state["opp_pts"][dest] < 2


def is_legal_from_point(state: Dict, src: int, die: int) -> bool:
    dest = src - die
    if dest >= 0:
        return state["opp_pts"][dest] < 2

    # bearing off
    if not all_in_home(state):
        return False
    # exact bear off
    if dest == -1 or src == die - 1:
        return True
    # oversize bear off: allowed only from highest occupied point
    # i.e., no checker on any higher point than src
    for j in range(src + 1, 24):
        if state["my_pts"][j] > 0:
            return False
    return True


def all_in_home(state: Dict) -> bool:
    if state["my_bar"] > 0:
        return False
    for i in range(6, 24):
        if state["my_pts"][i] > 0:
            return False
    return True


def apply_move(state: Dict, src, die: int) -> None:
    if src == "B":
        state["my_bar"] -= 1
        dest = 24 - die
    else:
        state["my_pts"][src] -= 1
        dest = src - die

    if dest >= 0:
        if state["opp_pts"][dest] == 1:
            state["opp_pts"][dest] = 0
            state["opp_bar"] += 1
        state["my_pts"][dest] += 1
    else:
        state["my_off"] += 1


def src_token(src) -> str:
    if src == "B":
        return "B"
    if src == "P":
        return "P"
    return f"A{src}"


# ----------------------------
# Evaluation
# ----------------------------

def evaluate_state(state: Dict) -> float:
    my_pts = state["my_pts"]
    opp_pts = state["opp_pts"]

    score = 0.0

    # Strong game-progress terms
    score += 120.0 * state["my_off"]
    score -= 115.0 * state["opp_off"]
    score -= 55.0 * state["my_bar"]
    score += 45.0 * state["opp_bar"]

    # Pip/race estimate
    my_pip = pip_count_my(state)
    opp_pip = pip_count_opp(state)
    race_phase = estimate_contact(state)
    score += (opp_pip - my_pip) * (0.22 if race_phase < 4 else 0.10)

    # Made points, home board, anchors
    my_home_points = 0
    opp_home_points = 0
    my_made = 0
    opp_made = 0
    my_blots = 0
    opp_blots = 0

    for i in range(24):
        m = my_pts[i]
        o = opp_pts[i]
        if m >= 2:
            my_made += 1
            if 0 <= i <= 5:
                my_home_points += 1
        elif m == 1:
            my_blots += 1

        if o >= 2:
            opp_made += 1
            if 18 <= i <= 23:
                opp_home_points += 1
        elif o == 1:
            opp_blots += 1

    score += 8.0 * my_made
    score -= 7.0 * opp_made
    score += 11.0 * my_home_points
    score -= 9.0 * opp_home_points

    # Prime building
    score += 12.0 * longest_prime(my_pts)
    score -= 10.0 * longest_prime_opp_view(opp_pts)

    # Anchors in opponent home board (points 18..23 for us)
    anchors = sum(1 for i in range(18, 24) if my_pts[i] >= 2)
    opp_anchors = sum(1 for i in range(0, 6) if opp_pts[i] >= 2)
    score += 7.0 * anchors
    score -= 6.0 * opp_anchors

    # Blot danger
    score -= blot_danger(state) * 14.0
    score += opp_blot_shots_for_us(state) * 10.0

    # Stacks penalty and distribution
    for i in range(24):
        if my_pts[i] >= 4:
            score -= (my_pts[i] - 3) * 2.2
        if opp_pts[i] >= 4:
            score += (opp_pts[i] - 3) * 1.5

    # Reward advanced checkers in contact game
    for i in range(24):
        score += my_pts[i] * (23 - i) * 0.12
        score -= opp_pts[i] * i * 0.10

    return score


def pip_count_my(state: Dict) -> int:
    total = state["my_bar"] * 25
    for i, c in enumerate(state["my_pts"]):
        total += c * (i + 1)
    return total


def pip_count_opp(state: Dict) -> int:
    total = state["opp_bar"] * 25
    for i, c in enumerate(state["opp_pts"]):
        total += c * (24 - i)
    return total


def estimate_contact(state: Dict) -> int:
    my_farthest = max((i for i, c in enumerate(state["my_pts"]) if c > 0), default=-1)
    opp_farthest_back = min((i for i, c in enumerate(state["opp_pts"]) if c > 0), default=24)
    if my_farthest < 0 or opp_farthest_back > 23:
        return 0
    # overlap/contact proxy
    return max(0, my_farthest - opp_farthest_back)


def longest_prime(arr: List[int]) -> int:
    best = cur = 0
    for i in range(24):
        if arr[i] >= 2:
            cur += 1
            if cur > best:
                best = cur
        else:
            cur = 0
    return best


def longest_prime_opp_view(arr: List[int]) -> int:
    # Opponent moves opposite direction, but contiguous blocks still matter similarly.
    return longest_prime(arr)


def blot_danger(state: Dict) -> float:
    danger = 0.0
    my_pts = state["my_pts"]
    opp_pts = state["opp_pts"]

    opp_positions = [i for i in range(24) if opp_pts[i] > 0]

    for i in range(24):
        if my_pts[i] != 1:
            continue
        shots = 0.0
        for j in opp_positions:
            # opponent moves upward j -> j + d
            d = i - j
            if 1 <= d <= 6:
                shots += min(2, opp_pts[j])
            elif 7 <= d <= 12:
                # crude two-die indirect shots
                shots += 0.35 * min(2, opp_pts[j])
        if 0 <= i <= 5:
            shots *= 0.8
        danger += shots
    if state["my_bar"] > 0:
        danger += 3.0 * state["my_bar"]
    return danger


def opp_blot_shots_for_us(state: Dict) -> float:
    val = 0.0
    my_pts = state["my_pts"]
    opp_pts = state["opp_pts"]
    my_positions = [i for i in range(24) if my_pts[i] > 0]

    for j in range(24):
        if opp_pts[j] != 1:
            continue
        shots = 0.0
        for i in my_positions:
            d = i - j
            # we move downward i -> i-die
            if 1 <= d <= 6:
                shots += min(2, my_pts[i])
            elif 7 <= d <= 12:
                shots += 0.25 * min(2, my_pts[i])
        val += shots
    if state["opp_bar"] > 0:
        val += 2.0 * state["opp_bar"]
    return val
