
import time

BAR = -1
PASS = -2
WIN_SCORE = 1000000.0

_MADE_WEIGHTS = (
    3.0, 4.5, 6.5, 8.5, 10.5, 9.5,
    8.5, 7.0, 6.0, 5.0, 4.0, 3.0,
    2.0, 2.2, 2.6, 3.2, 4.2, 5.2,
    6.2, 8.0, 10.0, 9.0, 6.5, 4.0,
)

_HOME_WEIGHTS = (1.0, 1.6, 2.5, 3.5, 4.6, 4.2)

_ANCHOR_WEIGHTS = (
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    5.0, 7.0, 10.0, 9.0, 6.0, 3.0,
)

_ROLLS = tuple(
    ((hi, lo), 1 if hi == lo else 2)
    for hi in range(1, 7)
    for lo in range(1, hi + 1)
)

_s = [0] * 24
_s[5] = 5
_s[7] = 3
_s[12] = 5
_s[23] = 2
_START_MY = tuple(_s)
_START_OPP = tuple(reversed(_START_MY))

_OPENING = {
    (3, 1): "H:A7,A5",
    (4, 2): "H:A7,A5",
    (5, 3): "H:A7,A5",
    (6, 1): "H:A12,A7",
    (6, 5): "H:A23,A17",
    (6, 4): "H:A23,A17",
    (6, 3): "H:A23,A17",
    (6, 2): "H:A23,A17",
    (5, 4): "H:A12,A23",
    (5, 2): "H:A12,A12",
    (4, 3): "H:A12,A12",
    (5, 1): "H:A12,A5",
    (4, 1): "H:A12,A5",
    (3, 2): "H:A23,A12",
    (2, 1): "H:A12,A5",
}


def policy(state: dict) -> str:
    try:
        actions = _legal_actions(state)
    except Exception:
        return "H:P,P"

    if not actions:
        return "H:P,P"
    if len(actions) == 1:
        return actions[0][0]

    book = _opening_book_move(state)
    if book is not None:
        for action, _, _ in actions:
            if action == book:
                return book

    try:
        start_time = time.perf_counter()
        scored = []
        for action, after_state, meta in actions:
            immediate = _heuristic(after_state)
            tie = _action_tiebreak(meta, action)
            scored.append((immediate + tie, immediate, tie, action, after_state, meta))

        scored.sort(key=lambda x: (x[0], x[3]), reverse=True)

        # In pure races, opponent reply search adds little; pip/off evaluation is more reliable.
        if not any(_has_contact_state(item[4]) for item in scored[:min(8, len(scored))]):
            return scored[0][3]

        n = len(scored)
        if n <= 18:
            k = n
        elif n <= 60:
            k = 18
        elif n <= 140:
            k = 14
        else:
            k = 10

        deadline = start_time + 0.86
        best_action = scored[0][3]
        best_value = -1.0e100
        evaluated = 0

        for rank, item in enumerate(scored[:k]):
            if time.perf_counter() > deadline:
                break
            _, immediate, tie, action, after_state, _ = item
            expected = _expected_after_opponent(after_state, deadline=deadline, fallback=immediate)
            value = 0.72 * expected + 0.28 * immediate + 0.25 * tie - 0.0001 * rank
            if value > best_value:
                best_value = value
                best_action = action
            evaluated += 1

        if evaluated:
            return best_action
        return scored[0][3]
    except Exception:
        return actions[0][0]


def _legal_actions(state):
    dice_obj = state.get("dice", [])
    try:
        dice = [int(x) for x in list(dice_obj)[:2]]
    except Exception:
        dice = []
    dice = [d for d in dice if 1 <= d <= 6]

    base = _copy_core_state(state)

    if len(dice) == 0:
        return [_pass_candidate(base, "H")]

    if len(dice) == 1:
        d = dice[0]
        starts = _legal_starts(base, d)
        if not starts:
            return [_pass_candidate(base, "H")]
        out = []
        for f in starts:
            st2, info = _apply_single(base, d, f)
            out.append(_candidate("H", f, PASS, [(d, f, info)], st2, d))
        out.sort(key=_legal_sort_key)
        return out

    d0, d1 = dice[0], dice[1]
    hi = d0 if d0 >= d1 else d1
    lo = d1 if d0 >= d1 else d0

    orders = [("H", hi, lo)] if hi == lo else [("H", hi, lo), ("L", lo, hi)]

    raw = []
    for order, first_die, second_die in orders:
        raw.extend(_gen_for_order(base, order, first_die, second_die, hi))

    if not raw:
        return [_pass_candidate(base, "H")]

    max_count = max(c[2]["count"] for c in raw)
    raw = [c for c in raw if c[2]["count"] == max_count]

    if max_count == 0:
        return [_pass_candidate(base, "H")]

    # If only one die can be used, the higher die must be used when possible.
    if max_count == 1 and hi > lo:
        high_exists = any(c[2]["used_high"] for c in raw)
        if high_exists:
            raw = [c for c in raw if c[2]["used_high"]]

    seen = set()
    out = []
    for c in raw:
        if c[0] not in seen:
            seen.add(c[0])
            out.append(c)

    out.sort(key=_legal_sort_key)
    return out


def _gen_for_order(base, order, d1, d2, hi_die):
    out = []
    firsts = _legal_starts(base, d1)

    if firsts:
        for f1 in firsts:
            st1, info1 = _apply_single(base, d1, f1)
            seconds = _legal_starts(st1, d2)
            if seconds:
                for f2 in seconds:
                    st2, info2 = _apply_single(st1, d2, f2)
                    out.append(_candidate(order, f1, f2, [(d1, f1, info1), (d2, f2, info2)], st2, hi_die))
            else:
                out.append(_candidate(order, f1, PASS, [(d1, f1, info1)], st1, hi_die))
    else:
        seconds = _legal_starts(base, d2)
        if seconds:
            for f2 in seconds:
                st2, info2 = _apply_single(base, d2, f2)
                out.append(_candidate(order, PASS, f2, [(d2, f2, info2)], st2, hi_die))
        else:
            out.append(_candidate(order, PASS, PASS, [], base, hi_die))

    return out


def _legal_starts(st, die):
    my = st["my_pts"]
    opp = st["opp_pts"]

    if st["my_bar"] > 0:
        dest = 24 - die
        if 0 <= dest < 24 and opp[dest] < 2:
            return [BAR]
        return []

    home_ready = _all_in_home_pts(my, st["my_bar"])
    starts = []

    for p in range(23, -1, -1):
        if my[p] <= 0:
            continue
        dest = p - die
        if dest >= 0:
            if opp[dest] < 2:
                starts.append(p)
        else:
            if home_ready and p <= 5:
                if die == p + 1 or not _has_higher_home_checker(my, p):
                    starts.append(p)

    return starts


def _apply_single(st, die, frm):
    my = st["my_pts"][:]
    opp = st["opp_pts"][:]
    my_bar = int(st["my_bar"])
    opp_bar = int(st["opp_bar"])
    my_off = int(st["my_off"])
    opp_off = int(st["opp_off"])

    hit = False
    off = False

    if frm == BAR:
        my_bar -= 1
        dest = 24 - die
        if opp[dest] == 1:
            opp[dest] = 0
            opp_bar += 1
            hit = True
        my[dest] += 1
    else:
        p = int(frm)
        my[p] -= 1
        dest = p - die
        if dest < 0:
            my_off += 1
            off = True
            dest = -1
        else:
            if opp[dest] == 1:
                opp[dest] = 0
                opp_bar += 1
                hit = True
            my[dest] += 1

    return {
        "my_pts": my,
        "opp_pts": opp,
        "my_bar": my_bar,
        "opp_bar": opp_bar,
        "my_off": my_off,
        "opp_off": opp_off,
        "dice": [],
    }, {"hit": hit, "off": off, "dest": dest}


def _candidate(order, f1, f2, move_infos, st, hi_die):
    moves = []
    hits = 0
    offs = 0
    used_high = False

    for die, frm, info in move_infos:
        moves.append((die, frm, info["dest"], info["hit"], info["off"]))
        if info["hit"]:
            hits += 1
        if info["off"]:
            offs += 1
        if die == hi_die:
            used_high = True

    action = order + ":" + _tok(f1) + "," + _tok(f2)
    meta = {
        "count": len(moves),
        "moves": tuple(moves),
        "hits": hits,
        "offs": offs,
        "used_high": used_high,
        "first_pass": (f1 == PASS),
    }
    return action, st, meta


def _pass_candidate(base, order):
    return (
        order + ":P,P",
        base,
        {
            "count": 0,
            "moves": (),
            "hits": 0,
            "offs": 0,
            "used_high": False,
            "first_pass": True,
        },
    )


def _tok(frm):
    if frm == BAR:
        return "B"
    if frm == PASS:
        return "P"
    return "A" + str(int(frm))


def _legal_sort_key(c):
    action, _, meta = c
    first_pass_bad = 1 if (meta["first_pass"] and meta["count"] > 0) else 0
    order_pref = 0 if action[0] == "H" else 1
    return (first_pass_bad, order_pref, action)


def _copy_core_state(state):
    return {
        "my_pts": _copy_points(state.get("my_pts", [0] * 24)),
        "opp_pts": _copy_points(state.get("opp_pts", [0] * 24)),
        "my_bar": int(state.get("my_bar", 0)),
        "opp_bar": int(state.get("opp_bar", 0)),
        "my_off": int(state.get("my_off", 0)),
        "opp_off": int(state.get("opp_off", 0)),
        "dice": [],
    }


def _copy_points(seq):
    try:
        pts = list(seq)
    except Exception:
        pts = [0] * 24
    if len(pts) < 24:
        pts = pts + [0] * (24 - len(pts))
    elif len(pts) > 24:
        pts = pts[:24]
    return pts


def _all_in_home_pts(pts, bar):
    if bar > 0:
        return False
    for i in range(6, 24):
        if pts[i] > 0:
            return False
    return True


def _has_higher_home_checker(pts, p):
    for q in range(p + 1, 6):
        if pts[q] > 0:
            return True
    return False


def _heuristic(st):
    my = st["my_pts"]
    opp_abs = st["opp_pts"]
    my_bar = int(st["my_bar"])
    opp_bar = int(st["opp_bar"])
    my_off = int(st["my_off"])
    opp_off = int(st["opp_off"])

    if my_off >= 15:
        return WIN_SCORE + 100.0 * (15 - opp_off)
    if opp_off >= 15:
        return -WIN_SCORE - 100.0 * (15 - my_off)

    opp = _reverse_pts(opp_abs)

    my_pips = _pip_count(my, my_bar)
    opp_pips = _pip_count(opp, opp_bar)
    pip_adv = opp_pips - my_pips

    contact = _has_contact_state(st)
    total_off = my_off + opp_off
    my_home_ready = _all_in_home_pts(my, my_bar)
    opp_home_ready = _all_in_home_pts(opp, opp_bar)

    if (not contact) or my_home_ready or opp_home_ready or total_off >= 8:
        pip_w = 3.0
    else:
        pip_w = 1.18

    score = pip_w * pip_adv

    off_w = 8.0 + (6.0 if total_off >= 10 else 0.0)
    score += off_w * (my_off - opp_off)

    if my_home_ready:
        score += 18.0
    if opp_home_ready:
        score -= 18.0

    score += 1.1 * (_outside_count(opp) - _outside_count(my))

    my_home_val = _home_board_value(my)
    opp_home_val = _home_board_value(opp)
    my_home_made = _home_made_count(my)
    opp_home_made = _home_made_count(opp)

    score += 30.0 * (opp_bar - my_bar)
    score += opp_bar * (6.5 * my_home_val + 10.0 * my_home_made)
    score -= my_bar * (6.5 * opp_home_val + 10.0 * opp_home_made)

    if opp_bar and my_home_made >= 5:
        score += 35.0 * opp_bar
    if my_bar and opp_home_made >= 5:
        score -= 35.0 * my_bar

    structure_mult = 1.0 if contact else 0.18
    if total_off >= 8:
        structure_mult *= 0.55
    score += structure_mult * (_structure_score(my) - _structure_score(opp))

    my_anchor = _anchor_value(my)
    opp_anchor = _anchor_value(opp)
    if contact:
        score += 0.45 * (my_anchor - opp_anchor)
        if pip_adv < -12:
            score += 0.45 * my_anchor
        if pip_adv > 12:
            score -= 0.45 * opp_anchor

        my_rev = _reverse_pts(my)
        score += _blockade_value(my, opp_abs, opp_bar)
        score -= _blockade_value(opp, my_rev, my_bar)

        my_danger = _blot_danger(my, opp_abs, opp_bar)
        opp_danger = _blot_danger(opp, my_rev, my_bar)

        risk_pen = 0.52
        attack_gain = 0.34
        if pip_adv > 12:
            risk_pen *= 1.25
            attack_gain *= 0.80
        elif pip_adv < -12:
            risk_pen *= 0.78
            attack_gain *= 1.25

        score += attack_gain * opp_danger - risk_pen * my_danger
    else:
        score += 0.08 * (my_anchor - opp_anchor)

    return score


def _expected_after_opponent(st, deadline=None, fallback=None):
    if st["my_off"] >= 15 or st["opp_off"] >= 15:
        return _heuristic(st)
    if fallback is None:
        fallback = _heuristic(st)

    opp_base = _flip_state(st, ())
    total = 0.0
    done_weight = 0

    for dice, weight in _ROLLS:
        if deadline is not None and done_weight > 0 and time.perf_counter() > deadline:
            total += (36 - done_weight) * fallback
            return total / 36.0

        opp_base["dice"] = dice
        opp_actions = _legal_actions(opp_base)

        best = -1.0e100
        for action, after_opp, meta in opp_actions:
            val = _heuristic(after_opp) + 0.05 * _action_tiebreak(meta, action)
            if val > best:
                best = val

        if best <= -1.0e90:
            best = _heuristic(opp_base)

        total += weight * (-best)
        done_weight += weight

    return total / 36.0


def _action_tiebreak(meta, action):
    tb = 0.02 * meta["count"]
    tb += 0.35 * meta["hits"]
    tb += 0.20 * meta["offs"]
    if meta["first_pass"] and meta["count"] > 0:
        tb -= 0.50
    if action and action[0] == "H":
        tb += 0.01
    return tb


def _pip_count(pts, bar):
    total = 25 * int(bar)
    for i, n in enumerate(pts):
        total += int(n) * (i + 1)
    return total


def _reverse_pts(pts):
    return list(reversed(pts))


def _outside_count(pts):
    return int(sum(pts[6:24]))


def _home_made_count(pts):
    c = 0
    for i in range(6):
        if pts[i] >= 2:
            c += 1
    return c


def _home_board_value(pts):
    val = 0.0
    for i in range(6):
        n = pts[i]
        if n >= 2:
            val += _HOME_WEIGHTS[i] + 0.25 * min(int(n) - 2, 2)
        elif n == 1:
            val += 0.15 * _HOME_WEIGHTS[i]
    return val


def _anchor_value(pts):
    val = 0.0
    for i in range(18, 24):
        if pts[i] >= 2:
            val += _ANCHOR_WEIGHTS[i] + 0.4 * min(int(pts[i]) - 2, 2)
    return val


def _structure_score(pts):
    score = 0.0
    made = [False] * 24

    for i, n in enumerate(pts):
        if n >= 2:
            made[i] = True
            score += _MADE_WEIGHTS[i]
            if n == 3:
                score += 1.0
            elif n == 4:
                score += 0.35
            elif n >= 5:
                score -= 1.2 * (int(n) - 4)
        elif n == 1:
            if 4 <= i <= 12:
                score += 0.55
            elif 13 <= i <= 17:
                score += 0.25

        if n > 3:
            pen = 0.7 * (int(n) - 3) * (int(n) - 3)
            if i >= 6:
                pen *= 1.35
            score -= pen

    home_made = sum(1 for i in range(6) if made[i])
    score += 2.3 * home_made * home_made

    i = 0
    while i < 24:
        if not made[i]:
            i += 1
            continue
        j = i
        while j < 24 and made[j]:
            j += 1
        length = j - i
        if length >= 2:
            run_score = 2.0 * length * length
            if length >= 4:
                run_score += 8.0
            if length >= 5:
                run_score += 20.0
            if length >= 6:
                run_score += 45.0
            if i < 12:
                run_score *= 1.15
            elif i >= 18:
                run_score *= 0.85
            score += run_score
        i = j

    return score


def _blockade_value(own_pts, enemy_pts, enemy_bar):
    made = [n >= 2 for n in own_pts]

    prefix = [0] * 25
    for i in range(24):
        prefix[i + 1] = prefix[i] + int(enemy_pts[i])

    score = 0.0
    i = 0
    while i < 24:
        if not made[i]:
            i += 1
            continue

        j = i
        while j < 24 and made[j]:
            j += 1

        length = j - i
        if length >= 2:
            trapped = int(enemy_bar) + prefix[i]
            if trapped > 0:
                t = trapped if trapped < 5 else 5
                run_score = t * (1.0 * length * length)
                if length >= 4:
                    run_score += 5.0 * t
                if length >= 5:
                    run_score += 12.0 * t
                if i < 12:
                    run_score *= 1.15
                score += run_score
        i = j

    return score


def _blot_danger(own_pts, enemy_pts, enemy_bar):
    danger = 0.0

    if enemy_bar > 0:
        open_entries = 0
        for i in range(6):
            if own_pts[i] < 2:
                open_entries += 1
        if open_entries == 0:
            board_mult = 0.0
        elif enemy_bar == 1:
            board_mult = 0.28
        else:
            board_mult = 0.08
    else:
        board_mult = 1.0

    for p in range(24):
        if own_pts[p] != 1:
            continue

        units = 0.0

        # Opponent bar enters on our A0..A5.
        if enemy_bar > 0 and p <= 5:
            units += 3.2 + 0.5 * min(int(enemy_bar), 3)

        if board_mult > 0.0:
            numbers = 0
            attackers = 0
            for d in range(1, 7):
                q = p - d
                if q >= 0 and enemy_pts[q] > 0:
                    numbers += 1
                    attackers += min(int(enemy_pts[q]), 3)
            if numbers:
                units += board_mult * (2.0 * numbers + 0.25 * attackers)

        if units:
            # Being hit near home is very expensive; being hit far back is less so.
            cost = 8.0 + 0.85 * (24 - p)
            if p <= 5:
                cost *= 1.20
            elif p >= 18:
                cost *= 0.75
            danger += units * cost

    return danger


def _has_contact_state(st):
    if st.get("my_bar", 0) > 0 or st.get("opp_bar", 0) > 0:
        return True

    my = st["my_pts"]
    opp = st["opp_pts"]

    max_my = -1
    for i in range(23, -1, -1):
        if my[i] > 0:
            max_my = i
            break

    min_opp = 24
    for i in range(24):
        if opp[i] > 0:
            min_opp = i
            break

    if max_my < 0 or min_opp > 23:
        return False
    return max_my > min_opp


def _flip_state(st, dice=()):
    return {
        "my_pts": list(reversed(st["opp_pts"])),
        "opp_pts": list(reversed(st["my_pts"])),
        "my_bar": int(st["opp_bar"]),
        "opp_bar": int(st["my_bar"]),
        "my_off": int(st["opp_off"]),
        "opp_off": int(st["my_off"]),
        "dice": list(dice),
    }


def _opening_book_move(state):
    dice = state.get("dice", [])
    try:
        if len(dice) != 2:
            return None
        d0 = int(dice[0])
        d1 = int(dice[1])
    except Exception:
        return None

    hi = d0 if d0 >= d1 else d1
    lo = d1 if d0 >= d1 else d0
    if hi == lo:
        return None

    if not _is_initial_position(state):
        return None

    return _OPENING.get((hi, lo))


def _is_initial_position(state):
    try:
        return (
            int(state.get("my_bar", 0)) == 0 and
            int(state.get("opp_bar", 0)) == 0 and
            int(state.get("my_off", 0)) == 0 and
            int(state.get("opp_off", 0)) == 0 and
            tuple(state.get("my_pts", ())) == _START_MY and
            tuple(state.get("opp_pts", ())) == _START_OPP
        )
    except Exception:
        return False
