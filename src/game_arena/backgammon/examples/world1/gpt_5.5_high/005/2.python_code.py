
import time

_DICE_VALUES = (1, 2, 3, 4, 5, 6)

_REPLY_ROLLS = []
for _a in _DICE_VALUES:
    for _b in range(_a, 7):
        _REPLY_ROLLS.append(((_a, _b), 1 if _a == _b else 2))


def policy(state: dict) -> str:
    actions = _generate_actions(state)
    if not actions:
        return "H:P,P"
    if len(actions) == 1:
        return actions[0][0]

    # Static scoring first: this is also the guaranteed fallback.
    scored = []
    for action, after in actions:
        scored.append((_evaluate_static(after), action, after))
    scored.sort(key=lambda x: x[0], reverse=True)

    best_static_score, best_static_action, _ = scored[0]

    # Shallow opponent-roll lookahead on the most promising moves.
    # It is deliberately capped so the function remains safe under 1 second.
    deadline = time.time() + 0.88

    candidate_map = {}
    base_limit = min(10, len(scored))
    for item in scored[:base_limit]:
        candidate_map[item[1]] = item

    # Always consider tactically forcing moves, even if static score ranks them
    # slightly below the top group.
    original_opp_bar = state.get("opp_bar", 0)
    original_my_off = state.get("my_off", 0)
    for item in scored[base_limit:]:
        after = item[2]
        if after["opp_bar"] > original_opp_bar or after["my_off"] > original_my_off:
            candidate_map[item[1]] = item
            if len(candidate_map) >= 16:
                break

    candidates = sorted(candidate_map.values(), key=lambda x: x[0], reverse=True)

    best_action = best_static_action
    best_value = -10**100
    best_tie_static = -10**100
    evaluated_any = False

    for static_score, action, after in candidates:
        if time.time() > deadline:
            break
        reply_value = _expected_after_opponent_reply(after, deadline)
        if reply_value is None:
            break
        evaluated_any = True

        # Mostly trust the reply search, with a little static tie-breaking.
        combined = 0.88 * reply_value + 0.12 * static_score
        if combined > best_value + 1e-9 or (
            abs(combined - best_value) <= 1e-9 and static_score > best_tie_static
        ):
            best_value = combined
            best_action = action
            best_tie_static = static_score

    return best_action if evaluated_any else best_static_action


# ---------------------------------------------------------------------------
# Legal move generation
# ---------------------------------------------------------------------------

def _copy_state(s):
    return {
        "my_pts": list(s["my_pts"]),
        "opp_pts": list(s["opp_pts"]),
        "my_bar": int(s["my_bar"]),
        "opp_bar": int(s["opp_bar"]),
        "my_off": int(s["my_off"]),
        "opp_off": int(s["opp_off"]),
        "dice": list(s.get("dice", [])),
    }


def _can_bear_off(s):
    return s["my_bar"] == 0 and sum(s["my_pts"][6:]) == 0


def _legal_starts(s, die):
    if die < 1 or die > 6:
        return []

    my_pts = s["my_pts"]
    opp_pts = s["opp_pts"]

    # Bar checkers must enter first.
    if s["my_bar"] > 0:
        dest = 24 - die
        if 0 <= dest < 24 and opp_pts[dest] < 2:
            return ["B"]
        return []

    can_bear = _can_bear_off(s)
    starts = []

    for p, count in enumerate(my_pts):
        if count <= 0:
            continue

        dest = p - die
        if dest >= 0:
            if opp_pts[dest] < 2:
                starts.append("A" + str(p))
        else:
            if can_bear:
                # Exact bear-off, or overshoot from the highest occupied point.
                if die == p + 1:
                    starts.append("A" + str(p))
                elif die > p + 1 and not any(my_pts[q] > 0 for q in range(p + 1, 6)):
                    starts.append("A" + str(p))

    return starts


def _apply_move(s, start, die):
    ns = _copy_state(s)

    if start == "P":
        return ns

    if start == "B":
        ns["my_bar"] -= 1
        dest = 24 - die
    else:
        p = int(start[1:])
        ns["my_pts"][p] -= 1
        dest = p - die

    if dest < 0:
        ns["my_off"] += 1
    else:
        if ns["opp_pts"][dest] == 1:
            ns["opp_pts"][dest] = 0
            ns["opp_bar"] += 1
        ns["my_pts"][dest] += 1

    return ns


def _generate_actions(state):
    dice = list(state.get("dice", []))
    if not dice:
        return [("H:P,P", _copy_state(state))]

    # One die remaining.
    if len(dice) == 1:
        d = dice[0]
        moves = _legal_starts(state, d)
        if not moves:
            return [("H:P,P", _copy_state(state))]
        out = []
        seen = set()
        for m in moves:
            after = _apply_move(state, m, d)
            action = "H:" + m + ",P"
            if action not in seen:
                seen.add(action)
                out.append((action, after))
        return out

    high = max(dice[0], dice[1])
    low = min(dice[0], dice[1])

    order_defs = [("H", (high, low))]
    if high != low:
        order_defs.append(("L", (low, high)))

    raw = []

    for order_char, dseq in order_defs:
        d1, d2 = dseq

        first_moves = _legal_starts(state, d1)
        if first_moves:
            first_options = [(m, _apply_move(state, m, d1)) for m in first_moves]
        else:
            first_options = [("P", _copy_state(state))]

        for f1, s1 in first_options:
            second_moves = _legal_starts(s1, d2)
            if second_moves:
                second_options = [(m, _apply_move(s1, m, d2)) for m in second_moves]
            else:
                second_options = [("P", _copy_state(s1))]

            for f2, s2 in second_options:
                used = (1 if f1 != "P" else 0) + (1 if f2 != "P" else 0)
                used_high = (f1 != "P" and d1 == high) or (f2 != "P" and d2 == high)
                action = order_char + ":" + f1 + "," + f2
                raw.append((action, s2, used, used_high, f1, f2))

    if not raw:
        return [("H:P,P", _copy_state(state))]

    max_used = max(r[2] for r in raw)

    if max_used == 0:
        return [("H:P,P", _copy_state(state))]

    filtered = [r for r in raw if r[2] == max_used]

    # If exactly one die can be played, the higher die must be played when possible.
    if max_used == 1 and high != low:
        if any(r[3] for r in filtered):
            filtered = [r for r in filtered if r[3]]

    # Prefer canonical one-move encodings with the move in FROM1, e.g. H:A5,P
    # or L:B,P, instead of leading-pass encodings such as H:P,A5.
    if max_used == 1 and any(r[4] != "P" for r in filtered):
        filtered = [r for r in filtered if r[4] != "P"]

    out = []
    seen = set()
    for action, after, _, _, _, _ in filtered:
        if action not in seen:
            seen.add(action)
            out.append((action, after))

    return out if out else [("H:P,P", _copy_state(state))]


# ---------------------------------------------------------------------------
# Evaluation and search
# ---------------------------------------------------------------------------

def _expected_after_opponent_reply(position_after_my_move, deadline):
    total = 0.0

    for roll, weight in _REPLY_ROLLS:
        if time.time() > deadline:
            return None

        opp_state = _flip_perspective(position_after_my_move, roll)
        opp_actions = _generate_actions(opp_state)

        best_for_opp = -10**100
        for _, opp_after in opp_actions:
            val = _evaluate_static(opp_after)
            if val > best_for_opp:
                best_for_opp = val

        total -= weight * best_for_opp

    return total / 36.0


def _flip_perspective(s, dice):
    return {
        "my_pts": list(reversed(s["opp_pts"])),
        "opp_pts": list(reversed(s["my_pts"])),
        "my_bar": int(s["opp_bar"]),
        "opp_bar": int(s["my_bar"]),
        "my_off": int(s["opp_off"]),
        "opp_off": int(s["my_off"]),
        "dice": list(dice),
    }


def _pip_counts(s):
    my_pip = s["my_bar"] * 25
    opp_pip = s["opp_bar"] * 25

    for i, c in enumerate(s["my_pts"]):
        my_pip += (i + 1) * c
    for i, c in enumerate(s["opp_pts"]):
        opp_pip += (24 - i) * c

    return my_pip, opp_pip


def _no_contact(s):
    if s["my_bar"] or s["opp_bar"]:
        return False

    my_occ = [i for i, c in enumerate(s["my_pts"]) if c > 0]
    opp_occ = [i for i, c in enumerate(s["opp_pts"]) if c > 0]

    if not my_occ or not opp_occ:
        return True

    # We move downward, opponent moves upward. If all our checkers are below all
    # opponent checkers, the armies have passed each other.
    return max(my_occ) < min(opp_occ)


def _evaluate_static(s):
    if s["my_off"] >= 15:
        return 100000.0
    if s["opp_off"] >= 15:
        return -100000.0

    my_pts = s["my_pts"]
    opp_pts = s["opp_pts"]

    my_pip, opp_pip = _pip_counts(s)
    pip_diff = opp_pip - my_pip
    off_diff = s["my_off"] - s["opp_off"]

    if _no_contact(s):
        rev_opp = list(reversed(opp_pts))
        score = 1.70 * pip_diff + 7.0 * off_diff
        score += _bearoff_shape(my_pts) - _bearoff_shape(rev_opp)
        score -= 0.35 * _stack_penalty(my_pts)
        score += 0.35 * _stack_penalty(rev_opp)
        return score

    rev_opp = list(reversed(opp_pts))
    rev_my = list(reversed(my_pts))

    score = 0.85 * pip_diff + 6.0 * off_diff

    my_home_made = sum(1 for i in range(6) if my_pts[i] >= 2)
    opp_home_made = sum(1 for i in range(18, 24) if opp_pts[i] >= 2)

    # Bar pressure and difficulty entering.
    score += 28.0 * s["opp_bar"]
    score -= 34.0 * s["my_bar"]
    score += 5.0 * s["opp_bar"] * my_home_made
    score -= 5.5 * s["my_bar"] * opp_home_made

    # Board structure, points, anchors, primes.
    score += _structure_score(my_pts)
    score -= _structure_score(rev_opp)
    score += _prime_score(my_pts)
    score -= _prime_score(rev_opp)

    # Blot danger. Own blot danger is immediate after our move; opponent blot
    # danger is useful but weighted lower because opponent moves next.
    my_vuln = _vulnerability_penalty(my_pts, opp_pts, s["opp_bar"])
    opp_vuln = _vulnerability_penalty(rev_opp, rev_my, s["my_bar"])
    score -= my_vuln
    score += 0.35 * opp_vuln

    # Small raw blot count term to prefer cleaner positions when hit odds are
    # similar.
    score -= 1.2 * sum(1 for c in my_pts if c == 1)
    score += 0.5 * sum(1 for c in opp_pts if c == 1)

    return score


def _point_value(i):
    # Point values from the perspective of a player moving 23 -> 0.
    # Home-board points are valuable for containment and bearoff; advanced
    # anchors in opponent's home board also matter in contact positions.
    if i <= 5:
        return 6.0 + 0.9 * i          # A5 is most valuable home-board point.
    if i <= 11:
        return 5.0 - 0.15 * (i - 6)   # Blocking/prime-building zone.
    if i <= 17:
        return 2.6                    # Outer-board points.
    anchor_vals = (5.2, 5.7, 4.6, 3.4, 2.3, 1.4)
    return anchor_vals[i - 18]


def _structure_score(pts):
    score = 0.0
    for i, c in enumerate(pts):
        if c >= 2:
            score += _point_value(i)
            score += 0.25 * min(c - 2, 2)
        if c >= 4:
            score -= 1.25 * (c - 3)
    return score


def _stack_penalty(pts):
    penalty = 0.0
    for c in pts:
        if c >= 4:
            penalty += c - 3
    return penalty


def _prime_score(pts):
    runs = []
    run = 0
    for i in range(24):
        if pts[i] >= 2:
            run += 1
        else:
            if run:
                runs.append(run)
            run = 0
    if run:
        runs.append(run)

    if not runs:
        return 0.0

    longest = max(runs)
    table = [0.0, 0.0, 2.0, 7.0, 15.0, 28.0, 45.0]
    score = table[min(longest, 6)]

    for r in runs:
        if r >= 3:
            score += 1.2 * (r - 2)

    return score


def _bearoff_shape(pts):
    if sum(pts[6:]) != 0:
        return 0.0

    score = 0.0
    for i, c in enumerate(pts[:6]):
        if c >= 4:
            score -= 0.65 * (c - 3)
        if c == 0 and any(pts[j] > 0 for j in range(i + 1, 6)):
            score -= 0.15
    return score


# ---------------------------------------------------------------------------
# Blot vulnerability
# ---------------------------------------------------------------------------

def _add_roll_pair(rolls, a, b):
    if 1 <= a <= 6 and 1 <= b <= 6:
        rolls.add((a, b))
        rolls.add((b, a))


def _add_any_roll_with_die(rolls, d):
    if 1 <= d <= 6:
        for x in _DICE_VALUES:
            rolls.add((d, x))
            rolls.add((x, d))


def _hit_chance_upward(vulnerable_pts, attacker_pts, attacker_bar, target):
    # vulnerable_pts[target] is a blot. Attacker moves upward, i.e. increasing
    # point index. Return approximate probability over 36 ordered rolls that the
    # blot can be hit.
    rolls = set()

    if not (0 <= target < 24):
        return 0.0

    # Attacker checker(s) on the bar enter at points 0..5.
    if attacker_bar > 0:
        direct_entry_die = target + 1
        if 1 <= direct_entry_die <= 6:
            _add_any_roll_with_die(rolls, direct_entry_die)

        if attacker_bar == 1:
            entry_dice = []
            for e in _DICE_VALUES:
                entry = e - 1
                if vulnerable_pts[entry] < 2:
                    entry_dice.append(e)

                    # Enter and continue with the same checker to hit target.
                    b = target - entry
                    if 1 <= b <= 6:
                        _add_roll_pair(rolls, e, b)

            # Enter the bar checker first, then hit from an existing point
            # checker with the other die.
            for d in _DICE_VALUES:
                src = target - d
                if 0 <= src < 24 and attacker_pts[src] > 0:
                    for e in entry_dice:
                        _add_roll_pair(rolls, e, d)

        return min(1.0, len(rolls) / 36.0)

    # Direct hits from board checkers.
    for d in _DICE_VALUES:
        src = target - d
        if 0 <= src < 24 and attacker_pts[src] > 0:
            _add_any_roll_with_die(rolls, d)

    # Two-die hits using one checker. Intermediate point may not be blocked by
    # two or more vulnerable checkers.
    lo = max(0, target - 12)
    for src in range(lo, target):
        if attacker_pts[src] <= 0:
            continue
        dist = target - src
        for a in _DICE_VALUES:
            b = dist - a
            if not (1 <= b <= 6):
                continue
            inter = src + a
            if inter != target and vulnerable_pts[inter] >= 2:
                continue
            _add_roll_pair(rolls, a, b)

    return min(1.0, len(rolls) / 36.0)


def _vulnerability_penalty(vulnerable_pts, attacker_pts, attacker_bar):
    attacker_home_made = sum(1 for i in range(18, 24) if attacker_pts[i] >= 2)
    penalty = 0.0

    for i, c in enumerate(vulnerable_pts):
        if c != 1:
            continue

        chance = _hit_chance_upward(vulnerable_pts, attacker_pts, attacker_bar, i)
        if chance <= 0.0:
            continue

        # Being hit near home is very expensive because the checker is sent back
        # to the bar from close to bearing off.
        cost = 12.0 + 0.65 * (24 - i)
        if i <= 5:
            cost += 5.0
        cost *= 1.0 + 0.07 * attacker_home_made

        penalty += chance * cost

    return penalty
