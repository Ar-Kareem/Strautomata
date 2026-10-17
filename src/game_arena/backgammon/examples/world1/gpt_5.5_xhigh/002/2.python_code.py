
import time

# All unordered rolls with their multiplicity among 36 ordered dice outcomes.
_ROLLS = [(a, b, 1 if a == b else 2) for a in range(1, 7) for b in range(a, 7)]

_HOME_WEIGHTS = (1.2, 3.4, 6.0, 9.0, 12.0, 10.0)
_OUTER_WEIGHTS = (8.0, 6.8, 5.8, 4.8, 4.0, 3.5,
                  4.2, 4.0, 3.6, 3.2, 2.8, 2.5)  # indices 6..17
_ANCHOR_WEIGHTS = (7.0, 9.0, 9.0, 7.0, 5.0, 3.0)  # indices 18..23
_PRIME_BONUS = (0.0, 0.0, 2.0, 6.0, 13.0, 24.0, 38.0)


def policy(state: dict) -> str:
    """Return a legal compact move string for the current position."""
    try:
        candidates = _generate_legal_actions(state)
    except Exception:
        return "H:P,P"

    if not candidates:
        return "H:P,P"

    fallback = candidates[0]["action"]
    if len(candidates) == 1:
        return fallback

    try:
        start_time = time.time()
        deadline = start_time + 0.82
        eval_cache = {}

        for cand in candidates:
            cand["_score"] = _eval_cached(cand["state"], eval_cache)

        candidates.sort(key=lambda c: c["_score"], reverse=True)

        # Immediate win.
        if candidates[0]["_score"] > 90000.0:
            return candidates[0]["action"]

        contact = _has_contact_state(state)
        if len(candidates) <= 10:
            top_n = len(candidates)
        else:
            top_n = min(len(candidates), 10 if contact else 7)

        top = candidates[:top_n]
        best = top[0]
        best_score = -1.0e100
        best_static = -1.0e100

        for cand in top:
            if time.time() < deadline:
                reply_score = _expected_after_opponent(cand["state"], eval_cache, deadline)
                final_score = 0.78 * reply_score + 0.22 * cand["_score"]
            else:
                final_score = cand["_score"]

            if (final_score > best_score + 1e-9 or
                    (abs(final_score - best_score) <= 1e-9 and cand["_score"] > best_static)):
                best = cand
                best_score = final_score
                best_static = cand["_score"]

        return best["action"]
    except Exception:
        return fallback


# ---------------------------------------------------------------------------
# Legal move generation
# ---------------------------------------------------------------------------

def _copy_state(s):
    dice = s.get("dice", [])
    if dice is None:
        dice = []
    return {
        "my_pts": list(s.get("my_pts", [0] * 24)),
        "opp_pts": list(s.get("opp_pts", [0] * 24)),
        "my_bar": int(s.get("my_bar", 0)),
        "opp_bar": int(s.get("opp_bar", 0)),
        "my_off": int(s.get("my_off", 0)),
        "opp_off": int(s.get("opp_off", 0)),
        "dice": list(dice),
    }


def _clean_dice(dice):
    if dice is None:
        return []
    out = []
    for d in dice:
        dd = int(d)
        if 1 <= dd <= 6:
            out.append(dd)
        if len(out) == 2:
            break
    return out


def _start_token(start):
    if start is None:
        return "P"
    if start == "B":
        return "B"
    return "A" + str(start)


def _all_in_home_points(my_pts, my_bar):
    return my_bar == 0 and not any(my_pts[6:])


def _legal_starts(state, die):
    """Legal start locations for one die in the current oriented position."""
    my_pts = state["my_pts"]
    opp_pts = state["opp_pts"]
    my_bar = state["my_bar"]

    if my_bar > 0:
        dest = 24 - die
        if 0 <= dest < 24 and opp_pts[dest] < 2:
            return ["B"]
        return []

    starts = []
    all_home = _all_in_home_points(my_pts, my_bar)

    for i in range(24):
        if my_pts[i] <= 0:
            continue

        dest = i - die
        if dest >= 0:
            if opp_pts[dest] < 2:
                starts.append(i)
        else:
            # Standard bearing-off rule: exact is always legal; overshoot is
            # legal only from the highest occupied point.
            if all_home:
                if die == i + 1 or (die > i + 1 and not any(my_pts[i + 1:])):
                    starts.append(i)

    return starts


def _land(ns, dest):
    if ns["opp_pts"][dest] == 1:
        ns["opp_pts"][dest] = 0
        ns["opp_bar"] += 1
    ns["my_pts"][dest] += 1


def _apply_single(state, start, die):
    ns = _copy_state(state)

    if start is None:
        return ns

    if start == "B":
        ns["my_bar"] -= 1
        dest = 24 - die
        _land(ns, dest)
        return ns

    i = int(start)
    ns["my_pts"][i] -= 1
    dest = i - die

    if dest >= 0:
        _land(ns, dest)
    else:
        ns["my_off"] += 1

    return ns


def _pass_candidate(base):
    return [{"action": "H:P,P", "state": _copy_state(base), "n": 0}]


def _raw_sequences_for_order(base, d1, d2, order_char):
    """Generate sequential plays for a fixed dice order, before global filtering."""
    out = []
    firsts = _legal_starts(base, d1)

    if firsts:
        for st1 in firsts:
            s1 = _apply_single(base, st1, d1)
            seconds = _legal_starts(s1, d2)

            if seconds:
                for st2 in seconds:
                    s2 = _apply_single(s1, st2, d2)
                    out.append({
                        "action": order_char + ":" + _start_token(st1) + "," + _start_token(st2),
                        "state": s2,
                        "n": 2,
                    })
            else:
                out.append({
                    "action": order_char + ":" + _start_token(st1) + ",P",
                    "state": s1,
                    "n": 1,
                })
    else:
        seconds = _legal_starts(base, d2)
        if seconds:
            for st2 in seconds:
                s2 = _apply_single(base, st2, d2)
                out.append({
                    "action": order_char + ":P," + _start_token(st2),
                    "state": s2,
                    "n": 1,
                })

    return out


def _state_key(s):
    return (
        tuple(s["my_pts"]),
        tuple(s["opp_pts"]),
        int(s["my_bar"]),
        int(s["opp_bar"]),
        int(s["my_off"]),
        int(s["opp_off"]),
    )


def _dedupe_candidates(cands):
    seen = set()
    out = []
    for cand in cands:
        key = _state_key(cand["state"])
        if key not in seen:
            seen.add(key)
            out.append(cand)
    return out


def _generate_legal_actions(state):
    """Generate legal actions and resulting states, enforcing mandatory dice use."""
    base = _copy_state(state)
    dice = _clean_dice(base.get("dice", []))

    if len(dice) == 0:
        return _pass_candidate(base)

    if len(dice) == 1:
        d = dice[0]
        starts = _legal_starts(base, d)
        if not starts:
            return _pass_candidate(base)

        cands = []
        for st in starts:
            ns = _apply_single(base, st, d)
            cands.append({
                "action": "H:" + _start_token(st) + ",P",
                "state": ns,
                "n": 1,
            })
        return _dedupe_candidates(cands)

    high = max(dice[0], dice[1])
    low = min(dice[0], dice[1])

    raw = []
    raw.extend(_raw_sequences_for_order(base, high, low, "H"))
    if high != low:
        raw.extend(_raw_sequences_for_order(base, low, high, "L"))

    max_used = max((cand["n"] for cand in raw), default=0)

    if max_used == 0:
        return _pass_candidate(base)

    if max_used == 2:
        return _dedupe_candidates([cand for cand in raw if cand["n"] == 2])

    # Exactly one die can be played. If the higher die is playable from the
    # original position, it must be used; otherwise use the lower die.
    if _legal_starts(base, high):
        desired = high
        order = "H"
    else:
        desired = low
        order = "H" if high == low else "L"

    starts = _legal_starts(base, desired)
    if not starts:
        return _pass_candidate(base)

    cands = []
    for st in starts:
        ns = _apply_single(base, st, desired)
        cands.append({
            "action": order + ":" + _start_token(st) + ",P",
            "state": ns,
            "n": 1,
        })
    return _dedupe_candidates(cands)


# ---------------------------------------------------------------------------
# Evaluation and shallow opponent lookahead
# ---------------------------------------------------------------------------

def _swap_perspective(s):
    """Transform a position so the opponent becomes 'my' side moving 23 -> 0."""
    return {
        "my_pts": list(reversed(s.get("opp_pts", [0] * 24))),
        "opp_pts": list(reversed(s.get("my_pts", [0] * 24))),
        "my_bar": int(s.get("opp_bar", 0)),
        "opp_bar": int(s.get("my_bar", 0)),
        "my_off": int(s.get("opp_off", 0)),
        "opp_off": int(s.get("my_off", 0)),
        "dice": list(s.get("dice", [])),
    }


def _eval_cached(s, cache):
    key = _state_key(s)
    if key in cache:
        return cache[key]
    val = _evaluate(s)
    cache[key] = val
    return val


def _expected_after_opponent(after_state, eval_cache, deadline):
    if after_state["my_off"] >= 15 or after_state["opp_off"] >= 15:
        return _eval_cached(after_state, eval_cache)

    opp_base = _swap_perspective(after_state)
    total = 0.0
    weight_done = 0

    for d1, d2, weight in _ROLLS:
        if time.time() > deadline:
            break

        opp_state = _copy_state(opp_base)
        opp_state["dice"] = [d1, d2]
        replies = _generate_legal_actions(opp_state)

        best_for_opp = -1.0e100
        for reply in replies:
            val = _eval_cached(reply["state"], eval_cache)
            if val > best_for_opp:
                best_for_opp = val

        total += weight * (-best_for_opp)
        weight_done += weight

    if weight_done == 36:
        return total / 36.0

    # If time ran out, fill the rest with the static value after our move.
    base_val = _eval_cached(after_state, eval_cache)
    return (total + (36 - weight_done) * base_val) / 36.0


def _has_contact_state(s):
    return _has_contact_arrays(
        s.get("my_pts", [0] * 24),
        s.get("opp_pts", [0] * 24),
        int(s.get("my_bar", 0)),
        int(s.get("opp_bar", 0)),
    )


def _has_contact_arrays(my_pts, opp_pts, my_bar, opp_bar):
    if my_bar > 0 or opp_bar > 0:
        return True

    my_hi = -1
    for i in range(23, -1, -1):
        if my_pts[i] > 0:
            my_hi = i
            break

    opp_lo = 24
    for i in range(24):
        if opp_pts[i] > 0:
            opp_lo = i
            break

    return my_hi > opp_lo


def _pip_counts(my_pts, opp_pts, my_bar, opp_bar):
    my_pips = my_bar * 25
    opp_pips = opp_bar * 25
    for i in range(24):
        my_pips += (i + 1) * my_pts[i]
        opp_pips += (24 - i) * opp_pts[i]
    return my_pips, opp_pips


def _crossovers(my_pts, opp_pts, my_bar, opp_bar):
    my_cross = my_bar * 5
    opp_cross = opp_bar * 5
    for i in range(24):
        my_cross += (i // 6 + 1) * my_pts[i]
        opp_cross += ((23 - i) // 6 + 1) * opp_pts[i]
    return my_cross, opp_cross


def _evaluate(s):
    my_pts = s["my_pts"]
    opp_pts = s["opp_pts"]
    my_bar = int(s["my_bar"])
    opp_bar = int(s["opp_bar"])
    my_off = int(s["my_off"])
    opp_off = int(s["opp_off"])

    if my_off >= 15:
        return 100000.0 + 10.0 * (15 - opp_off)
    if opp_off >= 15:
        return -100000.0 - 10.0 * (15 - my_off)

    contact = _has_contact_arrays(my_pts, opp_pts, my_bar, opp_bar)
    rev_opp = list(reversed(opp_pts))
    rev_my = list(reversed(my_pts))

    my_all_home = my_bar == 0 and not any(my_pts[6:])
    opp_all_home = opp_bar == 0 and not any(rev_opp[6:])

    my_pips, opp_pips = _pip_counts(my_pts, opp_pts, my_bar, opp_bar)
    my_cross, opp_cross = _crossovers(my_pts, opp_pts, my_bar, opp_bar)

    score = 0.0

    pip_weight = 1.38 if not contact else 0.52
    if my_all_home and opp_all_home:
        pip_weight = 1.58
    score += pip_weight * (opp_pips - my_pips)

    cross_weight = 0.72 if not contact else 0.28
    score += cross_weight * (opp_cross - my_cross)

    off_weight = 4.2 if not contact else 3.4
    score += off_weight * (my_off - opp_off)

    # Bar pressure and closed-board value.
    opp_entry_blocks = sum(1 for i in range(6) if my_pts[i] >= 2)
    my_entry_blocks = sum(1 for i in range(18, 24) if opp_pts[i] >= 2)

    if opp_bar:
        score += opp_bar * (18.0 + 5.0 * opp_entry_blocks)
        if opp_entry_blocks == 6:
            score += 90.0 * opp_bar
    if my_bar:
        score -= my_bar * (22.0 + 5.5 * my_entry_blocks)
        if my_entry_blocks == 6:
            score -= 100.0 * my_bar

    structure_weight = 1.0 if contact else 0.22
    score += structure_weight * (
        _side_structure(my_pts, contact) - _side_structure(rev_opp, contact)
    )

    if contact:
        score += 0.80 * (
            _blockade_score(my_pts, opp_pts) -
            _blockade_score(rev_opp, rev_my)
        )

        # The side to move next is the opponent, so our blots are immediately
        # dangerous; opponent blots are useful but less immediate.
        my_risk = _blot_risk(my_pts, opp_pts, opp_bar)
        opp_risk = _blot_risk(rev_opp, rev_my, my_bar)
        score -= 1.08 * my_risk
        score += 0.32 * opp_risk

    if my_all_home:
        score += 7.0 + 1.0 * my_off
    if opp_all_home:
        score -= 7.0 + 1.0 * opp_off

    return float(score)


def _side_structure(pts, contact):
    made = [pts[i] >= 2 for i in range(24)]
    score = 0.0

    for i, w in enumerate(_HOME_WEIGHTS):
        if made[i]:
            score += w

    for k, w in enumerate(_OUTER_WEIGHTS):
        i = 6 + k
        if made[i]:
            score += w

    anchor_scale = 1.0 if contact else 0.15
    for k, w in enumerate(_ANCHOR_WEIGHTS):
        i = 18 + k
        if made[i]:
            score += anchor_scale * w

    run = 0
    longest = 0
    for m in made:
        if m:
            run += 1
            if run > longest:
                longest = run
        else:
            run = 0
    if longest > 6:
        longest = 6
    score += _PRIME_BONUS[longest]

    home_made = sum(1 for i in range(6) if made[i])
    score += 0.7 * home_made * home_made

    for i, n in enumerate(pts):
        if n >= 3 and i <= 17:
            score += min(n - 2, 2) * 0.45
        if n > 5:
            score -= (n - 5) * (2.2 + 0.15 * (i // 6))
        if n == 1:
            if 6 <= i <= 12:
                score += 0.35
            elif 13 <= i <= 17:
                score += 0.15

    # Early ace/deuce stacks are inflexible unless we are already bearing off.
    if contact and any(pts[6:]):
        score -= 0.75 * pts[0] + 0.35 * pts[1]

    return score


def _blockade_score(block_pts, victim_pts):
    """Value made points/primes in front of opposing checkers."""
    made = [block_pts[i] >= 2 for i in range(24)]
    total = 0.0

    for j in range(24):
        n = victim_pts[j]
        if n <= 0:
            continue

        best = 0
        run = 0
        first_dist = 25
        found = False

        for i in range(j + 1, 24):
            if made[i]:
                if not found:
                    first_dist = i - j
                    found = True
                run += 1
                if run > best:
                    best = run
            else:
                run = 0

        if best >= 2:
            if first_dist <= 6:
                closeness = 1.0
            else:
                closeness = max(0.25, 1.0 - 0.055 * (first_dist - 6))
            total += n * (best - 1) * (best - 1) * closeness

    return total


def _prob_any_number(n):
    if n <= 0:
        return 0.0
    if n >= 6:
        return 1.0
    # Probability that at least one of two dice is in a set of n numbers.
    return (12.0 * n - n * n) / 36.0


def _blot_risk(player_pts, enemy_pts, enemy_bar):
    """
    Approximate probability-weighted cost of this side's blots being hit by the
    opponent on the next roll. Orientation: player moves down, enemy moves up.
    """
    total = 0.0
    enemy_bar = int(enemy_bar)

    if enemy_bar == 0:
        board_factor = 1.0
    elif enemy_bar == 1:
        board_factor = 0.35
    else:
        board_factor = 0.08

    for i in range(24):
        if player_pts[i] != 1:
            continue

        bar_nums = set()
        board_nums = set()
        combo_pairs = set()

        # Hits while entering from the bar: opponent enters on indices 0..5.
        if enemy_bar > 0:
            if i <= 5:
                bar_nums.add(i + 1)

            # Enter, then continue with the other die to hit this blot.
            if i <= 11:
                for entry_die in range(1, 7):
                    entry = entry_die - 1
                    step = i - entry
                    if 1 <= step <= 6 and player_pts[entry] < 2:
                        combo_pairs.add((entry_die, step))

        # Direct and two-die board shots from lower indices.
        for j in range(i):
            if enemy_pts[j] <= 0:
                continue

            dist = i - j
            if 1 <= dist <= 6:
                board_nums.add(dist)
            elif 7 <= dist <= 12:
                for a in range(1, 7):
                    b = dist - a
                    if 1 <= b <= 6:
                        mid = j + a
                        if mid < 24 and player_pts[mid] < 2:
                            combo_pairs.add((a, b))

        p_bar = _prob_any_number(len(bar_nums)) if enemy_bar > 0 else 0.0
        p_board = _prob_any_number(len(board_nums)) * board_factor
        p_direct = 1.0 - (1.0 - p_bar) * (1.0 - p_board)

        combo_factor = board_factor
        if enemy_bar == 1:
            combo_factor = max(combo_factor, 0.60)
        p_combo = min(0.60, (len(combo_pairs) / 36.0) * combo_factor)

        risk = min(0.95, p_direct + (1.0 - p_direct) * 0.55 * p_combo)
        if risk <= 0.0:
            continue

        # Being hit near home loses many pips; back blots are less costly.
        severity = 4.0 + 0.90 * (24 - i)
        if i <= 5:
            severity += 5.0
        if i >= 18:
            severity -= 1.5
        if severity < 3.0:
            severity = 3.0

        total += risk * severity

    return total
