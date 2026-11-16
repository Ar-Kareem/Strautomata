
import time

_ROLLS = tuple((a, b, 1 if a == b else 2) for a in range(1, 7) for b in range(a, 7))


class _SearchTimeout(Exception):
    pass


def policy(state: dict) -> str:
    """
    Return a legal Backgammon move string in the required compact format.
    """
    best_action = "H:P,P"
    try:
        candidates = _generate_legal_actions(state)
    except Exception:
        return _ultra_fallback(state)

    if not candidates:
        return "H:P,P"

    best_action = candidates[0][0]
    if len(candidates) == 1:
        return best_action

    try:
        scored = []
        for action, result in candidates:
            scored.append((_static_eval(result), action, result))
        scored.sort(key=lambda x: x[0], reverse=True)

        best_action = scored[0][1]
        best_score = -1.0e100

        n = len(scored)
        if n <= 10:
            top_n = n
        elif n <= 35:
            top_n = min(n, 18)
        else:
            top_n = min(n, 14)

        deadline = time.perf_counter() + 0.86

        for imm, action, result in scored[:top_n]:
            if imm > 90000.0:
                return action
            if time.perf_counter() > deadline:
                break

            exp_after_opp = _opponent_reply_expectation(result, deadline)
            combined = 0.35 * imm + 0.65 * exp_after_opp

            if combined > best_score:
                best_score = combined
                best_action = action

        return best_action

    except _SearchTimeout:
        return best_action
    except Exception:
        return best_action


# ---------------------------------------------------------------------
# Legal move generation
# ---------------------------------------------------------------------

def _pts24(v):
    try:
        arr = list(v)
    except Exception:
        arr = []
    if len(arr) < 24:
        arr = arr + [0] * (24 - len(arr))
    out = []
    for x in arr[:24]:
        try:
            out.append(int(x))
        except Exception:
            out.append(0)
    return out


def _dice_list(v):
    try:
        seq = list(v)
    except Exception:
        return []
    out = []
    for x in seq:
        try:
            d = int(x)
        except Exception:
            continue
        if 1 <= d <= 6:
            out.append(d)
        if len(out) >= 2:
            break
    return out


def _copy_state(s):
    return {
        "my_pts": _pts24(s.get("my_pts", [0] * 24)),
        "opp_pts": _pts24(s.get("opp_pts", [0] * 24)),
        "my_bar": int(s.get("my_bar", 0)),
        "opp_bar": int(s.get("opp_bar", 0)),
        "my_off": int(s.get("my_off", 0)),
        "opp_off": int(s.get("opp_off", 0)),
        "dice": _dice_list(s.get("dice", [])),
    }


def _token(start):
    if start == -1:
        return "B"
    return "A" + str(start)


def _all_in_home_pts(my_pts, my_bar):
    if my_bar > 0:
        return False
    for i in range(6, 24):
        if my_pts[i] > 0:
            return False
    return True


def _opp_all_in_home_pts(opp_pts, opp_bar):
    if opp_bar > 0:
        return False
    for i in range(18):
        if opp_pts[i] > 0:
            return False
    return True


def _can_bear_off_from(my_pts, i, d):
    # Exact bear-off.
    if d == i + 1:
        return True

    # Over-bear only from the highest occupied home-board point.
    if d > i + 1:
        for j in range(i + 1, 6):
            if my_pts[j] > 0:
                return False
        return True

    return False


def _legal_starts(s, d):
    my = s["my_pts"]
    opp = s["opp_pts"]

    # Bar checkers must enter first.
    if s["my_bar"] > 0:
        dest = 24 - d
        if 0 <= dest < 24 and opp[dest] < 2:
            return [-1]
        return []

    starts = []
    home = _all_in_home_pts(my, s["my_bar"])

    for i, c in enumerate(my):
        if c <= 0:
            continue

        dest = i - d
        if dest >= 0:
            if opp[dest] < 2:
                starts.append(i)
        else:
            if home and i <= 5 and _can_bear_off_from(my, i, d):
                starts.append(i)

    return starts


def _apply_move(s, start, d):
    my = s["my_pts"][:]
    opp = s["opp_pts"][:]
    my_bar = s["my_bar"]
    opp_bar = s["opp_bar"]
    my_off = s["my_off"]
    opp_off = s["opp_off"]

    if start == -1:
        my_bar -= 1
        dest = 24 - d
    else:
        my[start] -= 1
        dest = start - d

    if dest < 0:
        my_off += 1
    else:
        if opp[dest] == 1:
            opp[dest] = 0
            opp_bar += 1
        my[dest] += 1

    return {
        "my_pts": my,
        "opp_pts": opp,
        "my_bar": my_bar,
        "opp_bar": opp_bar,
        "my_off": my_off,
        "opp_off": opp_off,
        "dice": s.get("dice", []),
    }


def _generate_legal_actions(raw_state):
    s = _copy_state(raw_state)
    dice = s["dice"]

    if len(dice) == 0:
        return [("H:P,P", s)]

    seen = {}

    def add(action, result):
        if action not in seen:
            seen[action] = result

    if len(dice) == 1:
        d = dice[0]
        starts = _legal_starts(s, d)
        if not starts:
            return [("H:P,P", s)]
        for st in starts:
            add("H:%s,P" % _token(st), _apply_move(s, st, d))
        return list(seen.items())

    hi = max(dice[0], dice[1])
    lo = min(dice[0], dice[1])

    # First try all two-die plays. If any exist, only those are legal.
    if hi == lo:
        orders = [("H", hi, lo)]
    else:
        orders = [("H", hi, lo), ("L", lo, hi)]

    for order, d1, d2 in orders:
        for st1 in _legal_starts(s, d1):
            s1 = _apply_move(s, st1, d1)
            for st2 in _legal_starts(s1, d2):
                s2 = _apply_move(s1, st2, d2)
                add("%s:%s,%s" % (order, _token(st1), _token(st2)), s2)

    if seen:
        return list(seen.items())

    # No two-die play exists. Higher die must be played if possible.
    high_starts = _legal_starts(s, hi)
    if high_starts:
        for st in high_starts:
            add("H:%s,P" % _token(st), _apply_move(s, st, hi))
        return list(seen.items())

    low_starts = _legal_starts(s, lo)
    if low_starts:
        for st in low_starts:
            add("L:%s,P" % _token(st), _apply_move(s, st, lo))
        return list(seen.items())

    return [("H:P,P", s)]


def _ultra_fallback(state):
    try:
        acts = _generate_legal_actions(state)
        if acts:
            return acts[0][0]
    except Exception:
        pass
    return "H:P,P"


# ---------------------------------------------------------------------
# Evaluation and shallow opponent lookahead
# ---------------------------------------------------------------------

def _pip_counts(s):
    my = s["my_pts"]
    opp = s["opp_pts"]
    my_pip = s["my_bar"] * 25
    opp_pip = s["opp_bar"] * 25

    for i in range(24):
        my_pip += my[i] * (i + 1)
        opp_pip += opp[i] * (24 - i)

    return my_pip, opp_pip


def _has_contact(my, opp, my_bar, opp_bar):
    if my_bar > 0 or opp_bar > 0:
        return True

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


def _prime_score(pts):
    total = 0.0
    run = 0
    for i in range(24):
        if pts[i] >= 2:
            run += 1
        else:
            if run >= 2:
                total += run * run * 0.90 + max(0, run - 3) * 3.0
            run = 0
    if run >= 2:
        total += run * run * 0.90 + max(0, run - 3) * 3.0
    return total


def _opp_attack_count(point, opp, opp_bar):
    # Opponent moves upward, so it attacks a point from lower indices.
    cnt = 0.0
    board_factor = 0.65 if opp_bar > 0 else 1.0

    for d in range(1, 7):
        src = point - d
        if src >= 0 and opp[src] > 0:
            cnt += board_factor * (1.0 + (0.20 if opp[src] >= 3 else 0.0))

    # Opponent on bar enters into our home board A0..A5.
    if opp_bar > 0 and 0 <= point <= 5:
        cnt += 1.5 + 0.5 * min(opp_bar, 2)

    return cnt


def _my_attack_count(point, my, my_bar):
    # We move downward, so we attack an opposing blot from higher indices.
    cnt = 0.0
    board_factor = 0.65 if my_bar > 0 else 1.0

    for d in range(1, 7):
        src = point + d
        if src <= 23 and my[src] > 0:
            cnt += board_factor * (1.0 + (0.20 if my[src] >= 3 else 0.0))

    # Our bar entry lands in A18..A23.
    if my_bar > 0 and 18 <= point <= 23:
        cnt += 1.5 + 0.5 * min(my_bar, 2)

    return cnt


def _opp_indirect_attack_count(point, opp):
    cnt = 0.0
    for dist in range(7, 13):
        src = point - dist
        if src >= 0 and opp[src] > 0:
            cnt += 0.20
    return cnt


def _my_indirect_attack_count(point, my):
    cnt = 0.0
    for dist in range(7, 13):
        src = point + dist
        if src <= 23 and my[src] > 0:
            cnt += 0.20
    return cnt


def _static_eval(s):
    my = s["my_pts"]
    opp = s["opp_pts"]
    my_bar = s["my_bar"]
    opp_bar = s["opp_bar"]
    my_off = s["my_off"]
    opp_off = s["opp_off"]

    if my_off >= 15:
        return 100000.0
    if opp_off >= 15:
        return -100000.0

    my_pip, opp_pip = _pip_counts(s)
    contact = _has_contact(my, opp, my_bar, opp_bar)

    # Pure race: prioritize pip count and borne-off checkers.
    if not contact:
        return (opp_pip - my_pip) * 3.0 + (my_off - opp_off) * 22.0

    score = 0.0
    all_my_home = _all_in_home_pts(my, my_bar)
    all_opp_home = _opp_all_in_home_pts(opp, opp_bar)

    pip_w = 0.90
    if all_my_home or all_opp_home:
        pip_w = 1.45

    score += (opp_pip - my_pip) * pip_w
    score += (my_off - opp_off) * 20.0

    my_home_made = sum(1 for i in range(6) if my[i] >= 2)
    opp_home_made = sum(1 for i in range(18, 24) if opp[i] >= 2)

    # Bars are tactically very important, especially with closed boards.
    score += opp_bar * (22.0 + 7.0 * my_home_made)
    score -= my_bar * (22.0 + 7.0 * opp_home_made)
    if opp_bar > 0 and my_home_made == 6:
        score += 60.0 * opp_bar
    if my_bar > 0 and opp_home_made == 6:
        score -= 60.0 * my_bar

    # Made points, anchors, and stack efficiency.
    for i, c in enumerate(my):
        if c >= 2:
            if i <= 5:
                score += 7.5 + 0.35 * i
            elif i <= 11:
                score += 4.0
            elif i <= 17:
                score += 2.6
            else:
                score += 2.0
                if my_pip > opp_pip:
                    score += 2.0

        if c >= 5 and not all_my_home:
            score -= (c - 4) * 1.25
        if i <= 1 and c > 2 and not all_my_home:
            score -= (c - 2) * 0.45

    for i, c in enumerate(opp):
        if c >= 2:
            if i >= 18:
                score -= 7.5 + 0.35 * (23 - i)
            elif i >= 12:
                score -= 4.0
            elif i >= 6:
                score -= 2.6
            else:
                score -= 2.0
                if opp_pip > my_pip:
                    score -= 2.0

        if c >= 5 and not all_opp_home:
            score += (c - 4) * 1.25
        if i >= 22 and c > 2 and not all_opp_home:
            score += (c - 2) * 0.45

    score += _prime_score(my) - _prime_score(opp)

    # Blot safety and attack potential.
    for i, c in enumerate(my):
        if c == 1:
            direct = _opp_attack_count(i, opp, opp_bar)
            indirect = _opp_indirect_attack_count(i, opp)
            hit_cost = 1.4 + max(0, 18 - i) * 0.27
            penalty = 0.55 + direct * (3.0 + hit_cost) + indirect * (1.0 + 0.35 * hit_cost)
            score -= penalty

    for i, c in enumerate(opp):
        if c == 1:
            direct = _my_attack_count(i, my, my_bar)
            indirect = _my_indirect_attack_count(i, my)
            hit_gain = 1.3 + max(0, i - 5) * 0.24
            reward = 0.55 + direct * (2.8 + hit_gain) + indirect * (0.9 + 0.30 * hit_gain)
            score += reward

    if all_my_home:
        score += my_off * 5.0
    if all_opp_home:
        score -= opp_off * 5.0

    return score


def _flip_state(s, dice=None):
    return {
        "my_pts": list(reversed(s["opp_pts"])),
        "opp_pts": list(reversed(s["my_pts"])),
        "my_bar": s["opp_bar"],
        "opp_bar": s["my_bar"],
        "my_off": s["opp_off"],
        "opp_off": s["my_off"],
        "dice": [] if dice is None else list(dice),
    }


def _opponent_reply_expectation(after_my_move, deadline=None):
    # View the board from the opponent's perspective. The opponent also moves
    # from index 23 down to 0 after reversing the board.
    base = _flip_state(after_my_move)
    total = 0.0

    for a, b, weight in _ROLLS:
        if deadline is not None and time.perf_counter() > deadline:
            raise _SearchTimeout()

        base["dice"] = [a, b]
        replies = _generate_legal_actions(base)

        best_for_opp = -1.0e100
        for _, res in replies:
            val = _static_eval(res)
            if val > best_for_opp:
                best_for_opp = val

        # Our evaluation is the negative of opponent-perspective evaluation.
        total += weight * (-best_for_opp)

    return total / 36.0
