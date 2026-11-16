
import time
from functools import lru_cache

# Heuristic value of made points for a player who moves from 23 down to 0.
# 0..5 are home-board points; 18..23 are advanced anchors.
_POINT_VALUE = (
    1.5, 2.5, 4.0, 6.0, 9.5, 8.5,
    7.5, 6.5, 5.0, 3.5, 2.5, 2.0,
    1.5, 2.0, 2.5, 3.5, 4.5, 5.0,
    5.5, 8.0, 8.5, 7.0, 5.0, 3.0
)

_ROLLS = tuple((a, b, 1 if a == b else 2) for a in range(1, 7) for b in range(a, 7))


def policy(state: dict) -> str:
    start_time = time.time()
    try:
        st = _state_from_dict(state)
        dice = _dice_from_state(state)
        actions = _legal_actions(st, dice)

        if not actions:
            return "H:P,P"
        if len(actions) == 1:
            return actions[0][0]

        scored = []
        for action, new_st in actions:
            scored.append((_eval_static(new_st), action, new_st))
        scored.sort(key=lambda x: x[0], reverse=True)

        # In contact positions, examine likely opponent replies for the best few
        # static candidates. In pure races, static pip/bearoff evaluation is enough.
        if _contact(st[0], st[1], st[2], st[3]) and len(scored) > 1:
            n = len(scored)
            if n > 250:
                top_n = 3
            elif n > 100:
                top_n = 5
            else:
                top_n = 8
            top_n = min(top_n, n)

            deadline = start_time + 0.86
            best_action = scored[0][1]
            best_value = -1.0e100
            looked = False

            for static_score, action, new_st in scored[:top_n]:
                if looked and time.time() > deadline:
                    break
                reply_value = _opponent_expectation(new_st)
                # Small static component keeps initiative features from being
                # washed out by the coarse opponent model.
                total = reply_value + 0.08 * static_score
                looked = True
                if total > best_value:
                    best_value = total
                    best_action = action

            if looked:
                return best_action

        return scored[0][1]

    except Exception:
        return _emergency_policy(state)


def _emergency_policy(state):
    """Fallback used only if evaluation code fails; still tries legal enumeration."""
    try:
        st = _state_from_dict(state)
        dice = _dice_from_state(state)
        actions = _legal_actions(st, dice)
        if actions:
            return actions[0][0]
    except Exception:
        pass
    return "H:P,P"


def _state_from_dict(state):
    return (
        _clean_points(state.get("my_pts", [0] * 24)),
        _clean_points(state.get("opp_pts", [0] * 24)),
        max(0, int(state.get("my_bar", 0))),
        max(0, int(state.get("opp_bar", 0))),
        max(0, int(state.get("my_off", 0))),
        max(0, int(state.get("opp_off", 0))),
    )


def _clean_points(seq):
    vals = list(seq)
    if len(vals) < 24:
        vals += [0] * (24 - len(vals))
    return tuple(max(0, int(vals[i])) for i in range(24))


def _dice_from_state(state):
    out = []
    for x in state.get("dice", []):
        try:
            d = int(x)
        except Exception:
            continue
        if 1 <= d <= 6:
            out.append(d)
    return out[:2]


def _fmt_start(s):
    if s == -1:
        return "B"
    if s is None:
        return "P"
    return "A" + str(s)


def _legal_actions(st, dice):
    ds = []
    for x in dice:
        d = int(x)
        if 1 <= d <= 6:
            ds.append(d)
    ds = ds[:2]

    if len(ds) == 0:
        return [("H:P,P", st)]

    if len(ds) == 1:
        d = ds[0]
        starts = _legal_starts(st, d)
        if not starts:
            return [("H:P,P", st)]
        out = []
        seen = set()
        for s in starts:
            ns = _apply_move(st, s, d)
            action = "H:" + _fmt_start(s) + ",P"
            if action not in seen:
                seen.add(action)
                out.append((action, ns))
        return out

    low = min(ds[0], ds[1])
    high = max(ds[0], ds[1])

    if high == low:
        orders = (("H", high, low),)
    else:
        orders = (("H", high, low), ("L", low, high))

    entries = []  # (number_of_checker_moves, first_die_used, action, resulting_state)

    for order, d1, d2 in orders:
        first_starts = _legal_starts(st, d1)
        for s1 in first_starts:
            st1 = _apply_move(st, s1, d1)
            second_starts = _legal_starts(st1, d2)
            if second_starts:
                for s2 in second_starts:
                    st2 = _apply_move(st1, s2, d2)
                    action = order + ":" + _fmt_start(s1) + "," + _fmt_start(s2)
                    entries.append((2, d1, action, st2))
            else:
                action = order + ":" + _fmt_start(s1) + ",P"
                entries.append((1, d1, action, st1))

    # If both dice can be played, all one-die moves are illegal.
    two_move = [e for e in entries if e[0] == 2]
    if two_move:
        return _dedup_entries(two_move)

    one_move = [e for e in entries if e[0] == 1]
    if one_move:
        # If only one die can be played, the higher die must be used when possible.
        if high != low:
            high_possible = bool(_legal_starts(st, high))
            required_die = high if high_possible else low
            one_move = [e for e in one_move if e[1] == required_die]
        return _dedup_entries(one_move)

    return [("H:P,P", st)]


def _dedup_entries(entries):
    out = []
    seen = set()
    for _, _, action, ns in entries:
        if action not in seen:
            seen.add(action)
            out.append((action, ns))
    return out


def _legal_starts(st, die):
    my, opp, my_bar, _, _, _ = st

    # Bar checkers must enter before anything else.
    if my_bar > 0:
        dest = 24 - die
        if 0 <= dest < 24 and opp[dest] < 2:
            return [-1]
        return []

    all_home = _all_home_down(my, my_bar)
    starts = []

    for p, c in enumerate(my):
        if c <= 0:
            continue

        dest = p - die

        if dest >= 0:
            if opp[dest] < 2:
                starts.append(p)
        else:
            # Standard bearoff rule: exact bearoff is always legal when all
            # checkers are home; overshoot is legal only from the highest
            # occupied point.
            if all_home and p <= 5:
                if die == p + 1:
                    starts.append(p)
                elif die > p + 1 and not any(my[p + 1:6]):
                    starts.append(p)

    return starts


def _apply_move(st, start, die):
    my, opp, my_bar, opp_bar, my_off, opp_off = st
    my = list(my)
    opp = list(opp)

    if start == -1:
        my_bar -= 1
        dest = 24 - die
    else:
        my[start] -= 1
        dest = start - die

    if dest < 0:
        my_off += 1
    else:
        if opp[dest] == 1:
            opp[dest] = 0
            opp_bar += 1
        my[dest] += 1

    return (tuple(my), tuple(opp), my_bar, opp_bar, my_off, opp_off)


def _all_home_down(pts, bar):
    return bar == 0 and sum(pts[6:]) == 0


def _home_made(pts):
    return sum(1 for i in range(6) if pts[i] >= 2)


def _pip_down(pts, bar):
    total = bar * 25
    for i, c in enumerate(pts):
        total += (i + 1) * c
    return total


def _contact(my, opp, my_bar, opp_bar):
    if my_bar > 0 or opp_bar > 0:
        return True

    max_my = -1
    min_opp = 24

    for i, c in enumerate(my):
        if c and i > max_my:
            max_my = i
    for i, c in enumerate(opp):
        if c and i < min_opp:
            min_opp = i

    return max_my > min_opp


def _swap_perspective(st):
    my, opp, my_bar, opp_bar, my_off, opp_off = st
    return (
        tuple(reversed(opp)),
        tuple(reversed(my)),
        opp_bar,
        my_bar,
        opp_off,
        my_off,
    )


def _opponent_expectation(st_after_our_move):
    if st_after_our_move[4] >= 15 or st_after_our_move[5] >= 15:
        return _eval_static(st_after_our_move)

    opp_st = _swap_perspective(st_after_our_move)
    total = 0.0
    for a, b, weight in _ROLLS:
        # _best_reply_score is from opponent perspective; negate it to get our value.
        total -= weight * _best_reply_score(opp_st, a, b)
    return total / 36.0


@lru_cache(maxsize=32768)
def _best_reply_score(opp_st, a, b):
    actions = _legal_actions(opp_st, (a, b))
    best = -1.0e100
    for _, ns in actions:
        val = _eval_static(ns)
        if val > best:
            best = val
    return best


@lru_cache(maxsize=65536)
def _eval_static(st):
    my, opp, my_bar, opp_bar, my_off, opp_off = st

    if my_off >= 15:
        return 1.0e9 + 1000.0 * (15 - opp_off)
    if opp_off >= 15:
        return -1.0e9 - 1000.0 * (15 - my_off)

    opp_m = tuple(reversed(opp))
    my_m = tuple(reversed(my))

    my_pips = _pip_down(my, my_bar)
    opp_pips = _pip_down(opp_m, opp_bar)

    contact = _contact(my, opp, my_bar, opp_bar)
    race = not contact

    pip_coeff = 2.30 if race else 1.15
    score = (opp_pips - my_pips) * pip_coeff
    score += (my_off - opp_off) * 3.0

    my_struct = _structure_score(my)
    opp_struct = _structure_score(opp_m)

    if race:
        score += 0.20 * (my_struct - opp_struct)
        score += 0.80 * (_bearoff_bonus(my, my_bar, my_off) -
                         _bearoff_bonus(opp_m, opp_bar, opp_off))
        return score

    my_home = _home_made(my)
    opp_home = _home_made(opp_m)

    score += my_struct - 0.90 * opp_struct

    # Closed/strong home boards matter most when a checker is on the bar.
    score += (my_home * my_home - opp_home * opp_home) * 0.90
    score += opp_bar * (22.0 + 5.5 * my_home)
    score -= my_bar * (24.0 + 5.5 * opp_home)

    if opp_bar and my_home >= 5:
        score += opp_bar * (15.0 if my_home == 5 else 70.0)
    if my_bar and opp_home >= 5:
        score -= my_bar * (18.0 if opp_home == 5 else 75.0)

    # Safety: avoid blots that can be hit; reward opponent blots, but less
    # strongly because future shots are uncertain.
    score -= _blot_penalty(my, opp, opp_bar, True)
    score += 0.42 * _blot_penalty(opp_m, my_m, my_bar, True)

    # If behind, advanced anchors are valuable; if clearly ahead, extra back
    # checkers are a liability.
    if my_pips > opp_pips + 15:
        for p in range(18, 24):
            if my[p] >= 2:
                score += 4.0
    elif opp_pips > my_pips + 15:
        for p in range(18, 24):
            if my[p] > 2:
                score -= (my[p] - 2) * 1.5

    if _all_home_down(my, my_bar):
        score += 10.0 + my_off * 2.0
    if _all_home_down(opp_m, opp_bar):
        score -= 10.0 + opp_off * 2.0

    return score


def _structure_score(pts):
    s = 0.0

    for i, c in enumerate(pts):
        if c >= 2:
            s += _POINT_VALUE[i]

        # Spares are useful; very tall stacks are inefficient.
        if c == 3:
            s += 0.8
        elif c == 4:
            s += 0.3
        elif c >= 5:
            s -= (c - 4) * (1.2 if i >= 6 else 0.6)
            if c >= 7:
                s -= (c - 6) * (c - 6) * 0.5

    s += _prime_score(pts)
    return s


def _prime_score(pts):
    score = 0.0
    run = 0
    for i in range(25):
        c = pts[i] if i < 24 else 0
        if c >= 2:
            run += 1
        else:
            if run >= 2:
                score += (run - 1) * run * 1.2
            if run >= 4:
                score += (run - 3) * 4.0
            run = 0
    return score


def _bearoff_bonus(pts, bar, off):
    if not _all_home_down(pts, bar):
        return 0.0

    s = 10.0 + off * 3.0

    # Small wastage penalty for many checkers buried on the lowest points.
    s -= max(0, pts[0] - 3) * 0.8
    s -= max(0, pts[1] - 3) * 0.5
    return s


def _blot_penalty(my, opp, opp_bar, contact):
    if not contact:
        return 0.0

    penalty = 0.0
    for p, c in enumerate(my):
        if c == 1:
            base = 0.7
            if p >= 18:
                base += 2.0
            elif p >= 12:
                base += 1.0
            if p <= 5:
                base += 0.8
            penalty += base + _danger_for_blot(p, my, opp, opp_bar)

    return penalty


def _danger_for_blot(p, my, opp, opp_bar):
    # Direct shots: opponent moves upward, so attackers are at p-d.
    direct_values = set()

    if opp_bar > 0 and 0 <= p <= 5:
        direct_values.add(p + 1)

    for d in range(1, 7):
        q = p - d
        if q >= 0 and opp[q] > 0:
            direct_values.add(d)

    n = len(direct_values)
    direct_rolls = 0 if n == 0 else 36 - (6 - n) * (6 - n)

    # Indirect shots using both dice. This is approximate but catches the
    # common tactical danger of blots within 7-12 pips.
    combo = 0

    lo = max(0, p - 12)
    for q in range(lo, p):
        if opp[q] <= 0:
            continue
        dist = p - q
        if not (2 <= dist <= 12):
            continue
        for a in range(1, 7):
            b = dist - a
            if 1 <= b <= 6:
                mid = q + a
                if mid == p or my[mid] < 2:
                    combo += 1

    # Opponent on the bar can sometimes enter and then hit an outer/home blot.
    if opp_bar > 0 and p <= 11:
        for entry_die in range(1, 7):
            entry = entry_die - 1
            second = p - entry
            if 1 <= second <= 6 and my[entry] < 2:
                combo += 1

    return direct_rolls * 0.38 + min(combo, 24) * 0.10
