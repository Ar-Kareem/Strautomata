
def policy(state: dict) -> str:
    actions = _generate_legal_results(state)
    if not actions:
        return "H:P,P"

    scored = []
    for move, result in actions:
        scored.append((_evaluate(result), move, result))

    scored.sort(key=lambda x: x[0], reverse=True)

    # Look ahead only on the most plausible moves to stay comfortably under time.
    if len(scored) <= 18:
        candidates = scored
    else:
        candidates = scored[:14]

    best_score = None
    best_move = candidates[0][1]

    for imm_score, move, result in candidates:
        exp_score = _expected_after_opponent(result)
        total = 0.85 * exp_score + 0.15 * imm_score
        if best_score is None or total > best_score:
            best_score = total
            best_move = move

    return best_move


def _clone_state(s):
    return {
        "my_pts": list(s.get("my_pts", [0] * 24)),
        "opp_pts": list(s.get("opp_pts", [0] * 24)),
        "my_bar": int(s.get("my_bar", 0)),
        "opp_bar": int(s.get("opp_bar", 0)),
        "my_off": int(s.get("my_off", 0)),
        "opp_off": int(s.get("opp_off", 0)),
        "dice": list(s.get("dice", [])),
    }


def _all_home(s):
    if s["my_bar"] > 0:
        return False
    for i in range(6, 24):
        if s["my_pts"][i]:
            return False
    return True


def _can_bear_from(s, i, d):
    if not _all_home(s):
        return False
    if d == i + 1:
        return True
    if d > i + 1:
        for j in range(i + 1, 6):
            if s["my_pts"][j] > 0:
                return False
        return True
    return False


def _legal_starts(s, d):
    starts = []

    if d is None:
        return starts

    if s["my_bar"] > 0:
        dest = 24 - d
        if 0 <= dest < 24 and s["opp_pts"][dest] < 2:
            starts.append("B")
        return starts

    for i in range(24):
        if s["my_pts"][i] <= 0:
            continue

        dest = i - d
        if dest >= 0:
            if s["opp_pts"][dest] < 2:
                starts.append(i)
        else:
            if _can_bear_from(s, i, d):
                starts.append(i)

    return starts


def _apply_start(s, start, d):
    ns = _clone_state(s)
    ns["dice"] = []

    if start == "B":
        ns["my_bar"] -= 1
        dest = 24 - d
    else:
        ns["my_pts"][start] -= 1
        dest = start - d

    if dest < 0:
        ns["my_off"] += 1
    else:
        if ns["opp_pts"][dest] == 1:
            ns["opp_pts"][dest] = 0
            ns["opp_bar"] += 1
        ns["my_pts"][dest] += 1

    return ns


def _tok(x):
    if x is None:
        return "P"
    if x == "B":
        return "B"
    return "A" + str(x)


def _generate_order_sequences(state, order_char, d1, d2):
    out = []
    firsts = _legal_starts(state, d1)

    if not firsts:
        move = order_char + ":P,P"
        out.append((move, 0, _clone_state(state)))
        return out

    for f in firsts:
        s1 = _apply_start(state, f, d1)
        seconds = _legal_starts(s1, d2)

        if seconds:
            for g in seconds:
                s2 = _apply_start(s1, g, d2)
                move = order_char + ":" + _tok(f) + "," + _tok(g)
                out.append((move, 2, s2))
        else:
            move = order_char + ":" + _tok(f) + ",P"
            out.append((move, 1, s1))

    return out


def _generate_legal_results(state):
    s = _clone_state(state)
    dice = list(s.get("dice", []))

    if len(dice) == 0:
        return [("H:P,P", s)]

    raw = []

    if len(dice) == 1:
        d = dice[0]
        starts = _legal_starts(s, d)
        if not starts:
            return [("H:P,P", s)]
        for f in starts:
            ns = _apply_start(s, f, d)
            raw.append(("H:" + _tok(f) + ",P", 1, ns))

    else:
        a, b = dice[0], dice[1]
        hi, lo = max(a, b), min(a, b)

        if hi == lo:
            raw.extend(_generate_order_sequences(s, "H", hi, lo))
        else:
            raw.extend(_generate_order_sequences(s, "H", hi, lo))
            raw.extend(_generate_order_sequences(s, "L", lo, hi))

        if not raw:
            return [("H:P,P", s)]

        max_moves = max(x[1] for x in raw)
        raw = [x for x in raw if x[1] == max_moves]

        # If exactly one die is playable, the higher die must be used if possible.
        if max_moves == 1 and hi != lo:
            high_plays = [x for x in raw if x[0][0] == "H"]
            if high_plays:
                raw = high_plays

    if not raw:
        return [("H:P,P", s)]

    dedup = {}
    for move, count, result in raw:
        if move not in dedup:
            dedup[move] = result

    return list(dedup.items())


def _pip_counts(s):
    my_pip = s["my_bar"] * 25
    opp_pip = s["opp_bar"] * 25

    for i, n in enumerate(s["my_pts"]):
        my_pip += (i + 1) * n

    for i, n in enumerate(s["opp_pts"]):
        opp_pip += (24 - i) * n

    return my_pip, opp_pip


def _has_contact(s):
    my_hi = -1
    opp_lo = 24

    for i in range(24):
        if s["my_pts"][i] > 0:
            my_hi = i
        if s["opp_pts"][i] > 0 and opp_lo == 24:
            opp_lo = i

    return my_hi > opp_lo


def _made_point_value_my(i):
    if i <= 5:
        return 7.0 + (5 - i) * 0.35
    if i <= 11:
        return 4.2
    if i <= 17:
        return 3.0
    return 3.6


def _made_point_value_opp(i):
    # Opponent's home board is our 18..23.
    if i >= 18:
        return 7.0 + (i - 18) * 0.35
    if i >= 12:
        return 4.2
    if i >= 6:
        return 3.0
    return 3.6


def _prime_bonus(points):
    best = 0
    cur = 0
    total = 0.0
    for n in points:
        if n >= 2:
            cur += 1
            if cur >= 3:
                total += cur * 1.8
            if cur > best:
                best = cur
        else:
            cur = 0
    if best >= 4:
        total += best * best * 1.2
    return total


def _my_blot_danger(s):
    danger = 0.0
    opp = s["opp_pts"]

    for i in range(24):
        if s["my_pts"][i] != 1:
            continue

        shots = 0
        for d in range(1, 7):
            src = i - d
            if src >= 0 and opp[src] > 0:
                shots += 1 if opp[src] == 1 else 2

        if s["opp_bar"] > 0 and i <= 5:
            shots += min(3, s["opp_bar"] + 1)

        if shots:
            hit_cost = 24 - i
            local = 1.0
            if i <= 5:
                local += 1.1
            elif i >= 18:
                local += 0.25
            danger += shots * (3.0 + 0.34 * hit_cost) * local

    return danger


def _opp_blot_opportunity(s):
    bonus = 0.0
    my = s["my_pts"]

    for i in range(24):
        if s["opp_pts"][i] != 1:
            continue

        shots = 0
        for d in range(1, 7):
            src = i + d
            if src < 24 and my[src] > 0:
                shots += 1 if my[src] == 1 else 2

        if s["my_bar"] > 0 and i >= 18:
            shots += min(3, s["my_bar"] + 1)

        if shots:
            hit_gain = i + 1
            bonus += shots * (2.5 + 0.25 * hit_gain)

    return bonus


def _evaluate(s):
    my_pip, opp_pip = _pip_counts(s)
    contact = _has_contact(s)
    pos_mult = 1.0 if contact else 0.22

    score = 0.0

    # Race and borne-off equity.
    score += (opp_pip - my_pip) * 2.15
    score += (s["my_off"] - s["opp_off"]) * 9.0

    # Bar tempo.
    score += s["opp_bar"] * 24.0
    score -= s["my_bar"] * 27.0

    # Made points and anchors.
    my_home_made = 0
    opp_home_made = 0

    for i in range(24):
        mn = s["my_pts"][i]
        on = s["opp_pts"][i]

        if mn >= 2:
            score += pos_mult * _made_point_value_my(i)
            if mn >= 3:
                score += pos_mult * min(3, mn - 2) * 0.7
            if i <= 5:
                my_home_made += 1

        if on >= 2:
            score -= pos_mult * _made_point_value_opp(i)
            if on >= 3:
                score -= pos_mult * min(3, on - 2) * 0.7
            if i >= 18:
                opp_home_made += 1

    score += pos_mult * _prime_bonus(s["my_pts"])
    score -= pos_mult * _prime_bonus(list(reversed(s["opp_pts"])))

    # Closed/strong boards matter greatly when someone is on the bar.
    score += s["opp_bar"] * my_home_made * 7.0
    score -= s["my_bar"] * opp_home_made * 7.5

    # Blots and tactical shots.
    if contact:
        score -= _my_blot_danger(s) * 0.95
        score += _opp_blot_opportunity(s) * 0.55

    # Prefer smoother bearing positions when all checkers are home.
    if _all_home(s):
        spares = 0.0
        for i in range(6):
            if s["my_pts"][i] > 0:
                spares += s["my_pts"][i] * (6 - i) * 0.12
        score += spares

    return score


def _flip_state(s, dice=None):
    return {
        "my_pts": list(reversed(s["opp_pts"])),
        "opp_pts": list(reversed(s["my_pts"])),
        "my_bar": s["opp_bar"],
        "opp_bar": s["my_bar"],
        "my_off": s["opp_off"],
        "opp_off": s["my_off"],
        "dice": list(s.get("dice", [])) if dice is None else list(dice),
    }


_ROLLS = []
for _a in range(1, 7):
    for _b in range(_a, 7):
        _w = 1 if _a == _b else 2
        _ROLLS.append((_a, _b, _w))


def _expected_after_opponent(after_my_move):
    # If game is over or nearly malformed, static evaluation is safest.
    if after_my_move.get("my_off", 0) >= 15:
        return _evaluate(after_my_move)

    total = 0.0

    for a, b, w in _ROLLS:
        opp_view = _flip_state(after_my_move, [a, b])
        replies = _generate_legal_results(opp_view)

        worst_for_us = None
        for _, opp_result in replies:
            back_to_us = _flip_state(opp_result, [])
            val = _evaluate(back_to_us)
            if worst_for_us is None or val < worst_for_us:
                worst_for_us = val

        if worst_for_us is None:
            worst_for_us = _evaluate(after_my_move)

        total += w * worst_for_us

    return total / 36.0
