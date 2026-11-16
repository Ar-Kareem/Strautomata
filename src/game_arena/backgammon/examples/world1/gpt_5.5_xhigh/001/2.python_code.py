
import time

# Point values are from the perspective of the side moving from A23 toward A0.
# Low points are our home board; high points are anchors in the opponent home board.
_POINT_WEIGHTS = [
    8, 12, 17, 23, 30, 24,
    12, 10, 8, 7, 6, 5,
    5, 6, 8, 10, 12, 15,
    22, 28, 26, 20, 14, 8,
]

_PRIME_TABLE = [0, 0, 6, 18, 42, 80, 140]

_DIRECT_PROB = [0.0] * 7
for _n in range(7):
    _DIRECT_PROB[_n] = (12.0 * _n - _n * _n) / 36.0


def policy(state: dict) -> str:
    """Return a legal move string in ORDER:FROM1,FROM2 format."""
    try:
        s = _copy_state(state)
        candidates = _generate_candidates(s)
        if not candidates:
            return "H:P,P"

        scored = []
        best_action = candidates[0][0]
        best_score = -10**100

        for action, next_state, _used in candidates:
            val = _evaluate(next_state)
            scored.append((val, action, next_state))
            if val > best_score:
                best_score = val
                best_action = action

        scored.sort(key=lambda x: x[0], reverse=True)

        # Limited opponent-response lookahead in contact positions.
        # It is deliberately conservative and time bounded; legal fallback is already known.
        if len(scored) > 1 and _has_contact(s["my_pts"], s["opp_pts"], s["my_bar"], s["opp_bar"]):
            try:
                start = time.perf_counter()
                deadline = start + 0.78

                if len(scored) <= 30:
                    top_n = 7
                elif len(scored) <= 100:
                    top_n = 5
                else:
                    top_n = 3

                looked = []
                for static_val, action, next_state in scored[:top_n]:
                    if time.perf_counter() > deadline:
                        break
                    reply_val = _expected_after_opponent(next_state, deadline)
                    if reply_val is None:
                        break
                    combined = 0.72 * reply_val + 0.28 * static_val
                    looked.append((combined, static_val, action))

                if looked:
                    looked.sort(reverse=True)
                    best_action = looked[0][2]
            except Exception:
                pass

        return best_action

    except Exception:
        # Last-resort legal fallback: try the legal generator only.
        try:
            candidates = _generate_candidates(_copy_state(state))
            if candidates:
                return candidates[0][0]
        except Exception:
            pass
        return "H:P,P"


def _points24(x):
    y = list(x) if x is not None else []
    if len(y) < 24:
        y += [0] * (24 - len(y))
    return [int(v) for v in y[:24]]


def _dice_list(s):
    out = []
    for x in s.get("dice", []):
        try:
            d = int(x)
        except Exception:
            continue
        if 1 <= d <= 6:
            out.append(d)
    return out[:2]


def _copy_state(s):
    return {
        "my_pts": _points24(s.get("my_pts", [0] * 24)),
        "opp_pts": _points24(s.get("opp_pts", [0] * 24)),
        "my_bar": int(s.get("my_bar", 0)),
        "opp_bar": int(s.get("opp_bar", 0)),
        "my_off": int(s.get("my_off", 0)),
        "opp_off": int(s.get("opp_off", 0)),
        "dice": _dice_list(s),
    }


def _all_in_home(pts, bar):
    if bar != 0:
        return False
    for i in range(6, 24):
        if pts[i] > 0:
            return False
    return True


def _can_bear_off_from(pts, i, d):
    if d == i + 1:
        return True
    if d > i + 1:
        for j in range(i + 1, 6):
            if pts[j] > 0:
                return False
        return True
    return False


def _legal_starts(s, d):
    if d < 1 or d > 6:
        return []

    my = s["my_pts"]
    opp = s["opp_pts"]

    # Bar checkers must enter first.
    if s["my_bar"] > 0:
        dest = 24 - d
        if 0 <= dest < 24 and opp[dest] < 2:
            return ["B"]
        return []

    starts = []
    all_home = _all_in_home(my, 0)

    for i, c in enumerate(my):
        if c <= 0:
            continue
        dest = i - d
        if dest >= 0:
            if opp[dest] < 2:
                starts.append("A" + str(i))
        else:
            if all_home and _can_bear_off_from(my, i, d):
                starts.append("A" + str(i))

    return starts


def _apply_single(s, start, d):
    ns = {
        "my_pts": s["my_pts"][:],
        "opp_pts": s["opp_pts"][:],
        "my_bar": s["my_bar"],
        "opp_bar": s["opp_bar"],
        "my_off": s["my_off"],
        "opp_off": s["opp_off"],
        "dice": s.get("dice", [])[:],
    }

    if start == "B":
        ns["my_bar"] -= 1
        dest = 24 - d
    else:
        i = int(start[1:])
        ns["my_pts"][i] -= 1
        dest = i - d

    if dest < 0:
        ns["my_off"] += 1
    else:
        if ns["opp_pts"][dest] == 1:
            ns["opp_pts"][dest] = 0
            ns["opp_bar"] += 1
        ns["my_pts"][dest] += 1

    return ns


def _pass_candidate(s):
    return [("H:P,P", _copy_state(s), tuple())]


def _generate_candidates(state):
    dice = _dice_list(state)

    if len(dice) == 0:
        return _pass_candidate(state)

    if len(dice) == 1:
        d = dice[0]
        out = []
        for st in _legal_starts(state, d):
            ns = _apply_single(state, st, d)
            out.append(("H:" + st + ",P", ns, (d,)))
        return _dedupe(out) if out else _pass_candidate(state)

    high = max(dice[0], dice[1])
    low = min(dice[0], dice[1])

    orders = [("H", (high, low))]
    if high != low:
        orders.append(("L", (low, high)))

    candidates = []

    for order_char, ds in orders:
        d1, d2 = ds
        first_starts = _legal_starts(state, d1)

        for st1 in first_starts:
            s1 = _apply_single(state, st1, d1)
            second_starts = _legal_starts(s1, d2)

            if second_starts:
                for st2 in second_starts:
                    s2 = _apply_single(s1, st2, d2)
                    candidates.append((order_char + ":" + st1 + "," + st2, s2, (d1, d2)))
            else:
                candidates.append((order_char + ":" + st1 + ",P", s1, (d1,)))

    if not candidates:
        return _pass_candidate(state)

    # Backgammon dice-use rule: use the maximum number of dice possible.
    max_used = max(len(c[2]) for c in candidates)
    candidates = [c for c in candidates if len(c[2]) == max_used]

    # If exactly one die can be used, the higher die must be used when possible.
    if max_used == 1 and high != low:
        high_moves = [c for c in candidates if c[2] and c[2][0] == high]
        if high_moves:
            candidates = high_moves

    return _dedupe(candidates)


def _dedupe(candidates):
    seen = set()
    out = []
    for c in candidates:
        if c[0] not in seen:
            seen.add(c[0])
            out.append(c)
    return out


def _pip_side(pts, bar):
    total = 25 * bar
    for i, c in enumerate(pts):
        total += (i + 1) * c
    return total


def _has_contact(my_pts, opp_pts, my_bar, opp_bar):
    if my_bar > 0 or opp_bar > 0:
        return True

    max_my = -1
    for i in range(23, -1, -1):
        if my_pts[i] > 0:
            max_my = i
            break

    min_opp = 24
    for i in range(24):
        if opp_pts[i] > 0:
            min_opp = i
            break

    return max_my > min_opp


def _home_block_count_side(pts):
    n = 0
    for i in range(6):
        if pts[i] >= 2:
            n += 1
    return n


def _point_value_side(pts, contact):
    total = 0.0
    for i, c in enumerate(pts):
        if c >= 2:
            w = _POINT_WEIGHTS[i]
            if not contact:
                if i >= 18:
                    w *= 0.12
                elif i >= 12:
                    w *= 0.18
                else:
                    w *= 0.30
            total += w
            if c == 3:
                total += 0.7
    return total


def _prime_value_side(pts, enemy_pts, enemy_bar, contact):
    if not contact:
        return 0.0

    prefix = [0] * 25
    for i in range(24):
        prefix[i + 1] = prefix[i] + enemy_pts[i]

    total = 0.0
    i = 0
    while i < 24:
        if pts[i] < 2:
            i += 1
            continue
        start = i
        while i < 24 and pts[i] >= 2:
            i += 1
        end = i
        length = end - start

        if length >= 2:
            base = _PRIME_TABLE[min(length, 6)]
            trapped = enemy_bar + prefix[start]
            mult = 0.75 + 0.12 * min(trapped, 5)
            if end <= 6 and enemy_bar > 0:
                mult += 0.10 * min(enemy_bar, 3)
            total += base * mult

    return total


def _anchor_extra_side(pts, contact, race_lead):
    if not contact:
        return 0.0

    val = 0.0
    made_anchor = False
    for i, w in ((18, 10), (19, 14), (20, 13), (21, 9), (22, 5), (23, 2)):
        if pts[i] >= 2:
            val += w
            made_anchor = True

    back = sum(pts[18:24])
    if back >= 2 and not made_anchor:
        val -= 8.0 + 1.5 * back
    elif back == 1:
        val -= 5.0

    # When racing ahead, back checkers/anchors should be escaped rather than cherished.
    if race_lead > 18 and back > 0:
        val -= min(18.0, 0.25 * race_lead) * (back / 3.0)

    return val


def _stack_penalty_side(pts, contact):
    pen = 0.0
    for i, c in enumerate(pts):
        if c >= 4:
            pen += (c - 3) * (c - 3) * 1.4
        if c >= 6:
            pen += (c - 5) * 3.0
        if contact and i <= 1 and c > 2:
            pen += (c - 2) * 2.0
        if contact and i >= 22 and c > 2:
            pen += (c - 2) * 1.5
    return pen


def _race_wastage_side(pts):
    pen = _stack_penalty_side(pts, False)

    # In bearoff races, very uneven low-point piles waste large dice.
    if sum(pts[6:]) == 0:
        for i in range(6):
            c = pts[i]
            if c > 3:
                pen += (c - 3) * (7 - i) * 0.35
    return pen


def _single_legal_for_mobility(pts, enemy_pts, i, d, all_home):
    dest = i - d
    if dest >= 0:
        return enemy_pts[dest] < 2
    if all_home:
        return _can_bear_off_from(pts, i, d)
    return False


def _mobility_side(pts, enemy_pts, bar):
    if bar > 0:
        open_entries = 0
        for d in range(1, 7):
            if enemy_pts[24 - d] < 2:
                open_entries += 1
        return open_entries - 1.5 * max(0, bar - 1)

    all_home = _all_in_home(pts, 0)
    m = 0.0
    for i, c in enumerate(pts):
        if c <= 0:
            continue
        factor = 1.0 if c == 1 else 1.25
        for d in range(1, 7):
            if _single_legal_for_mobility(pts, enemy_pts, i, d, all_home):
                m += factor
    return m


def _clear_combo_orders(start, target, blockers):
    # Enemy moves upward from start to target using two dice.
    dist = target - start
    count = 0
    for a in range(1, 7):
        b = dist - a
        if 1 <= b <= 6:
            mid = start + a
            if 0 <= mid < 24 and blockers[mid] >= 2:
                continue
            count += 1
    return count


def _bar_combo_orders_to_target(target, blockers):
    # Enemy enters from bar onto e = die-1, then moves upward to target.
    count = 0
    for entry_die in range(1, 7):
        e = entry_die - 1
        second = target - e
        if 1 <= second <= 6 and blockers[e] < 2:
            count += 1
    return count


def _vulnerability_side(pts, enemy_pts, enemy_bar):
    enemy_home_blocks = 0
    for i in range(18, 24):
        if enemy_pts[i] >= 2:
            enemy_home_blocks += 1

    pen = 0.0

    for i, c in enumerate(pts):
        if c != 1:
            continue

        direct_nums = set()
        combo_orders = 0

        # Enemy checker(s) on bar enter in our home board and may hit blots there.
        if enemy_bar > 0:
            if i <= 5:
                direct_nums.add(i + 1)
            elif i <= 11:
                combo_orders += min(enemy_bar, 2) * _bar_combo_orders_to_target(i, pts)

        # Enemy board checkers move upward, so only checkers below the blot can hit it.
        for j in range(i):
            ec = enemy_pts[j]
            if ec <= 0:
                continue
            dist = i - j
            if dist <= 6:
                direct_nums.add(dist)
            elif dist <= 12:
                combo_orders += min(ec, 2) * _clear_combo_orders(j, i, pts)

        n = min(6, len(direct_nums))
        chance = _DIRECT_PROB[n]
        if combo_orders > 0:
            chance += min(0.45, (combo_orders / 36.0) * 0.55)
        if chance > 0.95:
            chance = 0.95

        pip_loss = 24 - i
        context = 13.0 + 1.30 * pip_loss + 4.5 * enemy_home_blocks
        if i <= 5:
            context += 10.0
        if i >= 18:
            context += 4.0

        # Some return-shot coverage makes a blot less costly.
        cover_nums = set()
        for j in range(i + 1, min(24, i + 7)):
            if pts[j] > 0:
                cover_nums.add(j - i)
        if i >= 18:
            die = 24 - i
            if 1 <= die <= 6:
                cover_nums.add(die)

        cover_chance = _DIRECT_PROB[min(6, len(cover_nums))]
        risk = chance * context * (1.0 - 0.15 * cover_chance)

        if chance > 0:
            risk += 1.8
        else:
            risk += 0.6

        pen += risk

    return pen


def _evaluate(s):
    my_pts = s["my_pts"]
    opp_pts = s["opp_pts"]
    my_bar = s["my_bar"]
    opp_bar = s["opp_bar"]
    my_off = s["my_off"]
    opp_off = s["opp_off"]

    if my_off >= 15:
        return 1_000_000.0
    if opp_off >= 15:
        return -1_000_000.0

    rev_my = my_pts[::-1]
    rev_opp = opp_pts[::-1]

    my_pip = _pip_side(my_pts, my_bar)
    opp_pip = _pip_side(rev_opp, opp_bar)
    race_lead = opp_pip - my_pip

    contact = _has_contact(my_pts, opp_pts, my_bar, opp_bar)

    my_home_blocks = _home_block_count_side(my_pts)
    opp_home_blocks = _home_block_count_side(rev_opp)

    score = 0.0

    if not contact:
        score += 7.0 * race_lead
        score += 14.0 * (my_off - opp_off)
        score += 30.0 * (opp_bar - my_bar)
        score -= _race_wastage_side(my_pts)
        score += 0.90 * _race_wastage_side(rev_opp)
        score += 0.10 * (_point_value_side(my_pts, False) - _point_value_side(rev_opp, False))
        return score

    # Contact-game evaluation.
    pip_weight = 2.6 if race_lead >= 0 else 1.7
    score += pip_weight * race_lead
    score += 10.0 * (my_off - opp_off)

    score += 38.0 * (opp_bar - my_bar)
    score += opp_bar * (16.0 * my_home_blocks + (70.0 if my_home_blocks == 6 else 0.0))
    score -= my_bar * (16.0 * opp_home_blocks + (70.0 if opp_home_blocks == 6 else 0.0))

    score += _point_value_side(my_pts, True)
    score -= _point_value_side(rev_opp, True)

    score += _prime_value_side(my_pts, opp_pts, opp_bar, True)
    score -= _prime_value_side(rev_opp, rev_my, my_bar, True)

    score += _anchor_extra_side(my_pts, True, race_lead)
    score -= _anchor_extra_side(rev_opp, True, -race_lead)

    my_vuln = _vulnerability_side(my_pts, opp_pts, opp_bar)
    opp_vuln = _vulnerability_side(rev_opp, rev_my, my_bar)

    safety_w = 1.0 + (0.25 if race_lead > 15 else 0.0)
    attack_w = 0.45 + (0.25 if race_lead < -15 else 0.0)

    score -= safety_w * my_vuln
    score += attack_w * opp_vuln

    score -= _stack_penalty_side(my_pts, True)
    score += 0.80 * _stack_penalty_side(rev_opp, True)

    score += 0.45 * (
        _mobility_side(my_pts, opp_pts, my_bar)
        - _mobility_side(rev_opp, rev_my, opp_bar)
    )

    return score


def _swap_perspective(s, dice=None):
    return {
        "my_pts": s["opp_pts"][::-1],
        "opp_pts": s["my_pts"][::-1],
        "my_bar": s["opp_bar"],
        "opp_bar": s["my_bar"],
        "my_off": s["opp_off"],
        "opp_off": s["my_off"],
        "dice": list(dice) if dice is not None else list(s.get("dice", [])),
    }


def _expected_after_opponent(s, deadline):
    opp_base = _swap_perspective(s)
    total = 0.0
    weight_total = 0

    for a in range(1, 7):
        for b in range(a, 7):
            if time.perf_counter() > deadline:
                return None

            weight = 1 if a == b else 2
            opp_state = {
                "my_pts": opp_base["my_pts"][:],
                "opp_pts": opp_base["opp_pts"][:],
                "my_bar": opp_base["my_bar"],
                "opp_bar": opp_base["opp_bar"],
                "my_off": opp_base["my_off"],
                "opp_off": opp_base["opp_off"],
                "dice": [a, b],
            }

            opp_candidates = _generate_candidates(opp_state)
            best_opp = -10**100

            for idx, (_act, opp_next, _used) in enumerate(opp_candidates):
                if idx % 32 == 0 and time.perf_counter() > deadline:
                    return None
                val = _evaluate(opp_next)
                if val > best_opp:
                    best_opp = val

            # Convert opponent-perspective score to our-perspective score.
            total += weight * (-best_opp)
            weight_total += weight

    if weight_total == 0:
        return None
    return total / weight_total
