
import math
from copy import deepcopy

def policy(state: dict) -> str:
    dice = state.get("dice", [])
    if not dice:
        return "H:P,P"

    try:
        moves = _legal_actions(state)
        if not moves:
            return "H:P,P"

        best = None
        best_score = -10**18

        for action, resulting_state in moves:
            sc = _evaluate(resulting_state)
            if sc > best_score:
                best_score = sc
                best = action

        return best if best is not None else moves[0][0]
    except Exception:
        return "H:P,P"


def _clone_state(s):
    return {
        "my_pts": list(s["my_pts"]),
        "opp_pts": list(s["opp_pts"]),
        "my_bar": int(s["my_bar"]),
        "opp_bar": int(s["opp_bar"]),
        "my_off": int(s["my_off"]),
        "opp_off": int(s["opp_off"]),
        "dice": list(s.get("dice", [])),
    }


def _all_home(s):
    if s["my_bar"] > 0:
        return False
    for i in range(6, 24):
        if s["my_pts"][i] > 0:
            return False
    return True


def _highest_checker(s):
    for i in range(23, -1, -1):
        if s["my_pts"][i] > 0:
            return i
    return -1


def _can_bear_from(s, pt, die):
    if not _all_home(s):
        return False
    dest = pt - die
    if dest >= 0:
        return False
    # Exact bearoff is always legal.
    if die == pt + 1:
        return True
    # Oversized die may bear off only the highest occupied point.
    return pt == _highest_checker(s)


def _legal_starts(s, die):
    starts = []

    # Bar has priority.
    if s["my_bar"] > 0:
        dest = 24 - die
        if 0 <= dest <= 23 and s["opp_pts"][dest] < 2:
            return ["B"]
        return []

    for pt in range(24):
        if s["my_pts"][pt] <= 0:
            continue

        dest = pt - die
        if dest >= 0:
            if s["opp_pts"][dest] < 2:
                starts.append("A%d" % pt)
        else:
            if _can_bear_from(s, pt, die):
                starts.append("A%d" % pt)

    return starts


def _apply_move(s, start, die):
    ns = _clone_state(s)

    if start == "P":
        return ns

    if start == "B":
        if ns["my_bar"] <= 0:
            return None
        src = None
        dest = 24 - die
        ns["my_bar"] -= 1
    else:
        if not start.startswith("A"):
            return None
        src = int(start[1:])
        if src < 0 or src > 23 or ns["my_pts"][src] <= 0:
            return None
        dest = src - die
        ns["my_pts"][src] -= 1

    if dest < 0:
        ns["my_off"] += 1
        return ns

    if dest > 23:
        return None

    if ns["opp_pts"][dest] >= 2:
        return None

    if ns["opp_pts"][dest] == 1:
        ns["opp_pts"][dest] = 0
        ns["opp_bar"] += 1

    ns["my_pts"][dest] += 1
    return ns


def _seqs_for_order(state, ordered_dice):
    out = []

    def rec(s, k, starts, used):
        if k >= len(ordered_dice):
            out.append((starts[:], used, s))
            return

        die = ordered_dice[k]
        legal = _legal_starts(s, die)

        if not legal:
            rec(s, k + 1, starts + ["P"], used)
        else:
            for st in legal:
                ns = _apply_move(s, st, die)
                if ns is not None:
                    rec(ns, k + 1, starts + [st], used + [(k, die, st)])

    rec(_clone_state(state), 0, [], [])
    return out


def _legal_actions(state):
    dice = list(state.get("dice", []))

    if len(dice) == 0:
        return [("H:P,P", _clone_state(state))]

    if len(dice) == 1:
        d = dice[0]
        res = []
        legal = _legal_starts(state, d)
        if not legal:
            return [("H:P,P", _clone_state(state))]
        for st in legal:
            ns = _apply_move(state, st, d)
            if ns is not None:
                res.append(("H:%s,P" % st, ns))
        return res if res else [("H:P,P", _clone_state(state))]

    d1, d2 = dice[0], dice[1]
    hi, lo = max(d1, d2), min(d1, d2)

    orders = []
    orders.append(("H", [hi, lo]))
    if hi != lo:
        orders.append(("L", [lo, hi]))

    candidates = []

    for code, odice in orders:
        for starts, used, ns in _seqs_for_order(state, odice):
            while len(starts) < 2:
                starts.append("P")
            action = "%s:%s,%s" % (code, starts[0], starts[1])
            candidates.append((action, ns, used, odice))

    if not candidates:
        return [("H:P,P", _clone_state(state))]

    max_used = max(len(c[2]) for c in candidates)
    candidates = [c for c in candidates if len(c[2]) == max_used]

    # If only one die can be used, the higher die must be used if possible.
    if max_used == 1 and hi != lo:
        high_possible = False
        for code, odice in orders:
            seqs = _seqs_for_order(state, odice)
            for starts, used, ns in seqs:
                if len(used) == 1 and used[0][1] == hi:
                    high_possible = True
                    break
            if high_possible:
                break

        if high_possible:
            candidates = [c for c in candidates if c[2] and c[2][0][1] == hi]

    return [(c[0], c[1]) for c in candidates]


def _pip_count_my(s):
    total = s["my_bar"] * 25
    for i, n in enumerate(s["my_pts"]):
        total += n * (i + 1)
    return total


def _pip_count_opp(s):
    # Opponent moves from 0 to 23, so distance off is 24 - i.
    total = s["opp_bar"] * 25
    for i, n in enumerate(s["opp_pts"]):
        total += n * (24 - i)
    return total


def _made_points_my(s):
    return [i for i, n in enumerate(s["my_pts"]) if n >= 2]


def _blot_risk(s, pt):
    # Opponent moves upward, so opposing checkers behind our blot are at lower indices.
    risk = 0.0
    for d in range(1, 7):
        j = pt - d
        if 0 <= j < 24 and s["opp_pts"][j] > 0:
            risk += s["opp_pts"][j] * (7 - d)
    # Blots in our home/outer board are generally more costly when hit.
    if pt <= 5:
        risk *= 1.6
    elif pt <= 11:
        risk *= 1.25
    return risk


def _evaluate(s):
    my_pip = _pip_count_my(s)
    opp_pip = _pip_count_opp(s)

    score = 0.0

    # Race and bearoff.
    score += (opp_pip - my_pip) * 3.0
    score += s["my_off"] * 120.0
    score -= s["opp_off"] * 120.0

    # Bar pressure.
    score += s["opp_bar"] * 95.0
    score -= s["my_bar"] * 120.0

    # Made points, especially home-board points.
    for i, n in enumerate(s["my_pts"]):
        if n >= 2:
            if i <= 5:
                score += 45.0 + (5 - i) * 3.0
            elif i <= 11:
                score += 22.0
            elif i <= 17:
                score += 14.0
            else:
                score += 8.0

        # Avoid very tall stacks except on low home points / bearing off.
        if n >= 4:
            score -= (n - 3) * 6.0

    # Opponent made home board is dangerous.
    for i, n in enumerate(s["opp_pts"]):
        if n >= 2:
            if i >= 18:
                score -= 35.0
            elif i >= 12:
                score -= 14.0

    # Blot safety.
    for i, n in enumerate(s["my_pts"]):
        if n == 1:
            score -= 10.0
            score -= _blot_risk(s, i) * 6.0

    # Opponent blots are tactical targets / weaknesses.
    for i, n in enumerate(s["opp_pts"]):
        if n == 1:
            score += 5.0

    # Prime/blocking structure: consecutive made points are valuable.
    made = set(_made_points_my(s))
    run = 0
    best_run = 0
    for i in range(24):
        if i in made:
            run += 1
            best_run = max(best_run, run)
        else:
            run = 0
    score += best_run * best_run * 8.0

    # Anchors in opponent home board, useful when behind.
    for i in range(18, 24):
        if s["my_pts"][i] >= 2:
            score += 18.0

    # Prefer clearing high points once bearing in/off.
    if _all_home(s):
        for i in range(6):
            score -= s["my_pts"][i] * i * 1.5
        score += s["my_off"] * 80.0
    else:
        # Encourage bringing back checkers from far side.
        for i in range(18, 24):
            score -= s["my_pts"][i] * 4.0

    return score
