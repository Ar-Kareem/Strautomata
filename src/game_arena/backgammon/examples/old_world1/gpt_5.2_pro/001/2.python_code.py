
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


# Direction convention used internally:
# dir = -1 : "downward" movement (i -> i-d), home board = points 0..5, enter from bar at 24-d
# dir = +1 : "upward" movement (i -> i+d), home board = points 18..23, enter from bar at d-1


@dataclass(frozen=True)
class MoveCand:
    move_str: str
    order: str
    from1: str
    from2: str
    # resulting state after applying the move under a specific direction model:
    next_state: dict


def _home_range(dirn: int) -> range:
    return range(0, 6) if dirn == -1 else range(18, 24)


def _opp_home_range(dirn: int) -> range:
    # Opponent moves opposite direction; their home is opposite end.
    return range(18, 24) if dirn == -1 else range(0, 6)


def _entry_point(die: int, dirn: int) -> int:
    return 24 - die if dirn == -1 else die - 1


def _can_bear_off(st: dict, dirn: int) -> bool:
    if st["my_bar"] > 0:
        return False
    my_pts = st["my_pts"]
    if dirn == -1:
        return sum(my_pts[6:24]) == 0
    else:
        return sum(my_pts[0:18]) == 0


def _bearoff_is_legal_from_point(my_pts: List[int], from_pt: int, die: int, dirn: int) -> bool:
    home = _home_range(dirn)
    if from_pt not in home:
        return False

    # Exact bear-off condition:
    if dirn == -1:
        # off beyond -1, exact when from_pt - die == -1  => from_pt == die-1
        exact = (from_pt == die - 1)
        if exact:
            return True
        # Overage: can bear off from the highest occupied point if die is bigger
        # Condition: no checkers on points higher than from_pt within home.
        if die > (from_pt + 1):
            highest = None
            for p in range(5, -1, -1):
                if my_pts[p] > 0:
                    highest = p
                    break
            return highest == from_pt
        return False
    else:
        # off beyond 23, exact when from_pt + die == 24 => from_pt == 24-die
        exact = (from_pt == 24 - die)
        if exact:
            return True
        # Overage: can bear off from the lowest occupied point if die is bigger.
        # Here lower indices are farther from bearing off.
        if die > (24 - from_pt):
            lowest = None
            for p in range(18, 24):
                if my_pts[p] > 0:
                    lowest = p
                    break
            return lowest == from_pt
        return False


def _legal_from_points_for_die(st: dict, die: int, dirn: int) -> List[int]:
    """
    Returns list of starting locations encoded as:
      -1 => Bar
      0..23 => board points
    """
    my_pts = st["my_pts"]
    opp_pts = st["opp_pts"]
    if die < 1 or die > 6:
        return []

    # Must enter from bar first if any on bar.
    if st["my_bar"] > 0:
        dest = _entry_point(die, dirn)
        if 0 <= dest <= 23 and opp_pts[dest] < 2:
            return [-1]
        return []

    can_bo = _can_bear_off(st, dirn)
    res = []
    for i in range(24):
        if my_pts[i] <= 0:
            continue
        dest = i + dirn * die
        if 0 <= dest <= 23:
            if opp_pts[dest] < 2:
                res.append(i)
        else:
            # Potential bear off
            if can_bo and _bearoff_is_legal_from_point(my_pts, i, die, dirn):
                res.append(i)
    return res


def _apply_single_move(st: dict, from_loc: int, die: int, dirn: int) -> dict:
    """
    Returns a NEW state dict after applying one move using (from_loc, die).
    Assumes the move is legal per our legality checker.
    """
    ns = {
        "my_pts": st["my_pts"][:],
        "opp_pts": st["opp_pts"][:],
        "my_bar": st["my_bar"],
        "opp_bar": st["opp_bar"],
        "my_off": st["my_off"],
        "opp_off": st["opp_off"],
        "dice": st.get("dice", [])[:],
    }

    if from_loc == -1:
        # From bar
        ns["my_bar"] -= 1
        dest = _entry_point(die, dirn)
    else:
        ns["my_pts"][from_loc] -= 1
        dest = from_loc + dirn * die

    if 0 <= dest <= 23:
        # Hit if exactly one opponent checker
        if ns["opp_pts"][dest] == 1:
            ns["opp_pts"][dest] = 0
            ns["opp_bar"] += 1
        ns["my_pts"][dest] += 1
    else:
        # Bear off
        ns["my_off"] += 1
    return ns


def _token_from_loc(loc: int) -> str:
    if loc == -1:
        return "B"
    if 0 <= loc <= 23:
        return f"A{loc}"
    return "P"


def _pip_count_my(st: dict, dirn: int) -> int:
    # Distance-to-bearoff approximation consistent with the chosen direction model.
    # Also counts bar as 25 pips.
    my_pts = st["my_pts"]
    if dirn == -1:
        # point i is i+1 pips away from off
        return st["my_bar"] * 25 + sum((i + 1) * my_pts[i] for i in range(24))
    else:
        # point i is (24-i) pips away from off
        return st["my_bar"] * 25 + sum((24 - i) * my_pts[i] for i in range(24))


def _pip_count_opp(st: dict, dirn: int) -> int:
    # Opponent moves opposite direction to us.
    opp_pts = st["opp_pts"]
    opp_dir = -dirn
    if opp_dir == -1:
        return st["opp_bar"] * 25 + sum((i + 1) * opp_pts[i] for i in range(24))
    else:
        return st["opp_bar"] * 25 + sum((24 - i) * opp_pts[i] for i in range(24))


def _longest_prime(my_pts: List[int]) -> int:
    # Longest consecutive run of made points (>=2 checkers).
    best = 0
    cur = 0
    for i in range(24):
        if my_pts[i] >= 2:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def _eval_state(prev: dict, st: dict, dirn: int) -> float:
    my_pts = st["my_pts"]
    opp_pts = st["opp_pts"]
    home = _home_range(dirn)
    opp_home = _opp_home_range(dirn)

    hits = st["opp_bar"] - prev["opp_bar"]

    my_pip = _pip_count_my(st, dirn)
    opp_pip = _pip_count_opp(st, dirn)

    made_pts = sum(1 for i in range(24) if my_pts[i] >= 2)
    home_made = sum(1 for i in home if my_pts[i] >= 2)
    anchors = sum(1 for i in opp_home if my_pts[i] >= 2)

    blots = [i for i in range(24) if my_pts[i] == 1]

    # Vulnerability: can opponent hit a blot next turn with one die?
    # Opponent direction is opposite; approximate "threat" by presence of any opponent checker
    # within 1..6 pips behind the blot (in opponent's moving direction).
    opp_dir = -dirn
    vuln = 0
    for p in blots:
        if opp_dir == +1:
            # opponent hits p from [p-6, p-1]
            a = max(0, p - 6)
            b = p - 1
            if b >= a:
                vuln += sum(1 for q in range(a, b + 1) if opp_pts[q] > 0)
        else:
            # opponent hits p from [p+1, p+6]
            a = p + 1
            b = min(23, p + 6)
            if b >= a:
                vuln += sum(1 for q in range(a, b + 1) if opp_pts[q] > 0)

    # If opponent is on the bar, blotting in our home board is especially bad (easy entry hits).
    home_blots = sum(1 for i in home if my_pts[i] == 1)
    home_blocks = sum(1 for i in home if my_pts[i] >= 2)

    prime_len = _longest_prime(my_pts)

    score = 0.0
    # Winning progress
    score += 180.0 * st["my_off"] - 170.0 * st["opp_off"]
    # Bar pressure
    score += 110.0 * st["opp_bar"] - 260.0 * st["my_bar"]
    # Immediate tactics
    score += 70.0 * hits
    # Structure
    score += 4.0 * made_pts + 6.0 * home_made + 6.0 * anchors
    score += 2.2 * (prime_len ** 2)
    # Race component
    score += -0.42 * my_pip + 0.18 * opp_pip
    # Risk management
    score -= 9.0 * len(blots)
    score -= 1.8 * vuln
    if st["opp_bar"] > 0:
        score += 14.0 * home_blocks * st["opp_bar"]
        score -= 22.0 * home_blots * st["opp_bar"]

    return score


def _generate_candidates_for_dir(state: dict, dirn: int) -> List[MoveCand]:
    dice = list(state.get("dice", []))
    if len(dice) == 0:
        return [MoveCand("H:P,P", "H", "P", "P", state)]
    if len(dice) == 1:
        d = dice[0]
        froms = _legal_from_points_for_die(state, d, dirn)
        if not froms:
            return [MoveCand("H:P,P", "H", "P", "P", state)]
        cands = []
        for f in froms:
            ns = _apply_single_move(state, f, d, dirn)
            s1 = _token_from_loc(f)
            mv = f"H:{s1},P"
            cands.append(MoveCand(mv, "H", s1, "P", ns))
        return cands

    # Two dice case:
    d1, d2 = dice[0], dice[1]
    high = max(d1, d2)
    low = min(d1, d2)

    def gen_sequences(first_die: int, second_die: int, order_char: str) -> List[MoveCand]:
        res = []
        first_froms = _legal_from_points_for_die(state, first_die, dirn)
        for f1 in first_froms:
            st1 = _apply_single_move(state, f1, first_die, dirn)
            second_froms = _legal_from_points_for_die(st1, second_die, dirn)
            for f2 in second_froms:
                st2 = _apply_single_move(st1, f2, second_die, dirn)
                t1 = _token_from_loc(f1)
                t2 = _token_from_loc(f2)
                mv = f"{order_char}:{t1},{t2}"
                res.append(MoveCand(mv, order_char, t1, t2, st2))
        return res

    both = []
    both.extend(gen_sequences(high, low, "H"))
    if high != low:
        both.extend(gen_sequences(low, high, "L"))

    if both:
        return both

    # Can't play both dice; must play the higher die if possible.
    high_froms = _legal_from_points_for_die(state, high, dirn)
    low_froms = _legal_from_points_for_die(state, low, dirn)

    cands = []
    if high_froms:
        for f in high_froms:
            ns = _apply_single_move(state, f, high, dirn)
            t = _token_from_loc(f)
            mv = f"H:{t},P"
            cands.append(MoveCand(mv, "H", t, "P", ns))
        return cands
    if low_froms:
        for f in low_froms:
            ns = _apply_single_move(state, f, low, dirn)
            t = _token_from_loc(f)
            mv = f"L:{t},P"
            cands.append(MoveCand(mv, "L", t, "P", ns))
        return cands

    return [MoveCand("H:P,P", "H", "P", "P", state)]


def _direction_plausibility(st: dict, dirn: int) -> float:
    """
    Heuristic to guess which direction model matches the engine's current player identity.
    Higher is more plausible.
    """
    my_pts = st["my_pts"]
    opp_pts = st["opp_pts"]
    home = _home_range(dirn)
    opp_home = _opp_home_range(dirn)

    my_onboard = max(1, 15 - st["my_off"] - st["my_bar"])
    opp_onboard = max(1, 15 - st["opp_off"] - st["opp_bar"])

    my_home_mass = sum(my_pts[i] for i in home) / my_onboard
    opp_home_mass = sum(opp_pts[i] for i in opp_home) / opp_onboard

    my_pip = _pip_count_my(st, dirn)
    opp_pip = _pip_count_opp(st, dirn)

    # Prefer the model where (a) our checkers are "more in home" as we bear off,
    # and (b) our pip count seems better relative to opponent given off counts.
    plaus = 0.0
    plaus += 6.0 * (my_home_mass - opp_home_mass)
    plaus += 0.25 * (opp_pip - my_pip)
    plaus += 2.0 * (st["my_off"] - st["opp_off"])
    # If we are on the bar, correctness of entry points matters a lot: reward any legal entry.
    if st["my_bar"] > 0:
        dice = st.get("dice", [])
        entry_possible = 0
        for d in dice:
            if _legal_from_points_for_die(st, d, dirn):
                entry_possible += 1
        plaus += 10.0 * entry_possible
    return plaus


def policy(state: Dict) -> str:
    # Generate candidates under both possible direction models.
    cands_down = _generate_candidates_for_dir(state, -1)
    cands_up = _generate_candidates_for_dir(state, +1)

    # Build maps for intersection of move strings (moves legal under both models).
    map_down = {c.move_str: c for c in cands_down}
    map_up = {c.move_str: c for c in cands_up}
    inter_keys = set(map_down.keys()) & set(map_up.keys())

    def pick_best(cands: List[MoveCand], dirn: int) -> MoveCand:
        best = None
        best_score = -1e100
        for c in cands:
            sc = _eval_state(state, c.next_state, dirn)
            # Deterministic tie-break: prefer lexicographically smaller move string.
            if (sc > best_score) or (abs(sc - best_score) < 1e-9 and (best is None or c.move_str < best.move_str)):
                best_score = sc
                best = c
        return best if best is not None else MoveCand("H:P,P", "H", "P", "P", state)

    # If we can find moves legal in both direction models, pick the one with best averaged evaluation.
    if inter_keys:
        best_mv = None
        best_score = -1e100
        for k in inter_keys:
            cd = map_down[k]
            cu = map_up[k]
            sc = 0.5 * _eval_state(state, cd.next_state, -1) + 0.5 * _eval_state(state, cu.next_state, +1)
            if (sc > best_score) or (abs(sc - best_score) < 1e-9 and (best_mv is None or k < best_mv)):
                best_score = sc
                best_mv = k
        return best_mv if best_mv is not None else "H:P,P"

    # Otherwise choose the more plausible direction model and pick best move there.
    plaus_down = _direction_plausibility(state, -1)
    plaus_up = _direction_plausibility(state, +1)

    # If one direction yields only pass but the other yields real moves, take the real one.
    down_only_pass = (len(cands_down) == 1 and cands_down[0].move_str == "H:P,P")
    up_only_pass = (len(cands_up) == 1 and cands_up[0].move_str == "H:P,P")

    if down_only_pass and not up_only_pass:
        return pick_best(cands_up, +1).move_str
    if up_only_pass and not down_only_pass:
        return pick_best(cands_down, -1).move_str

    if plaus_up > plaus_down:
        return pick_best(cands_up, +1).move_str
    else:
        return pick_best(cands_down, -1).move_str
