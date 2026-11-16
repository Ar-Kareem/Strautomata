
# Backgammon arena policy
# Implements: policy(state: dict) -> str

BAR = -1
PASS = None


def policy(state: dict) -> str:
    """
    Return a legal move string in the form '<ORDER>:<FROM1>,<FROM2>'.
    """
    try:
        candidates = _generate_candidates(state)
    except Exception:
        # Last-resort fallback. This should almost never be reached.
        return "H:P,P"

    if not candidates:
        return "H:P,P"

    # If evaluation has any unexpected issue, returning the first generated
    # candidate is still a legal move.
    best_action = candidates[0][0]
    best_score = -10**100

    try:
        for cand in candidates:
            action, after, moves, dice_used, order = cand
            score = _evaluate(after) + _candidate_bonus(state, cand)
            if score > best_score:
                best_score = score
                best_action = action
    except Exception:
        return best_action

    return best_action


# ---------------------------------------------------------------------------
# Legal move generation
# ---------------------------------------------------------------------------

def _points24(x):
    try:
        p = list(x)
    except Exception:
        p = []
    if len(p) < 24:
        p = p + [0] * (24 - len(p))
    elif len(p) > 24:
        p = p[:24]
    return [int(v) for v in p]


def _int_get(state, key, default=0):
    try:
        return int(state.get(key, default))
    except Exception:
        return default


def _normal_state(state):
    return {
        "my_pts": _points24(state.get("my_pts", [0] * 24)),
        "opp_pts": _points24(state.get("opp_pts", [0] * 24)),
        "my_bar": _int_get(state, "my_bar", 0),
        "opp_bar": _int_get(state, "opp_bar", 0),
        "my_off": _int_get(state, "my_off", 0),
        "opp_off": _int_get(state, "opp_off", 0),
    }


def _token(start):
    if start is PASS:
        return "P"
    if start == BAR:
        return "B"
    return "A" + str(int(start))


def _all_in_home(st):
    return st["my_bar"] == 0 and sum(st["my_pts"][6:24]) == 0


def _can_bear_off_from(my_pts, start, die):
    # Exact bear-off.
    if die == start + 1:
        return True
    # Oversized die may bear off only the highest occupied point.
    if die > start + 1:
        for j in range(start + 1, 6):
            if my_pts[j] > 0:
                return False
        return True
    return False


def _legal_starts(st, die):
    die = int(die)
    if die < 1 or die > 6:
        return []

    my = st["my_pts"]
    opp = st["opp_pts"]

    # Bar checkers must enter first.
    if st["my_bar"] > 0:
        dest = 24 - die
        if 0 <= dest < 24 and opp[dest] < 2:
            return [BAR]
        return []

    starts = []
    home_ready = _all_in_home(st)

    for i in range(24):
        if my[i] <= 0:
            continue

        dest = i - die
        if dest >= 0:
            if opp[dest] < 2:
                starts.append(i)
        else:
            if home_ready and i < 6 and _can_bear_off_from(my, i, die):
                starts.append(i)

    return starts


def _apply_single(st, die, start):
    die = int(die)
    my = st["my_pts"][:]
    opp = st["opp_pts"][:]
    my_bar = st["my_bar"]
    opp_bar = st["opp_bar"]
    my_off = st["my_off"]

    if start == BAR:
        my_bar -= 1
        dest = 24 - die
    else:
        start = int(start)
        my[start] -= 1
        dest = start - die

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
        "opp_off": st["opp_off"],
    }


def _dedupe(cands):
    out = []
    seen = set()
    for c in cands:
        if c[0] not in seen:
            seen.add(c[0])
            out.append(c)
    return out


def _pass_candidate(st):
    return ("H:P,P", st, (), (), "H")


def _generate_candidates(state):
    st = _normal_state(state)

    raw_dice = state.get("dice", [])
    try:
        dice = [int(d) for d in list(raw_dice) if 1 <= int(d) <= 6]
    except Exception:
        dice = []

    if not dice:
        return [_pass_candidate(st)]

    # The arena format supports up to two checker moves.
    if len(dice) > 2:
        dice = dice[:2]

    if len(dice) == 1:
        d = dice[0]
        starts = _legal_starts(st, d)
        if not starts:
            return [_pass_candidate(st)]

        cands = []
        for m in starts:
            after = _apply_single(st, d, m)
            action = "H:%s,P" % _token(m)
            cands.append((action, after, (m,), (d,), "H"))
        return _dedupe(cands)

    d0, d1 = dice[0], dice[1]
    hi = max(d0, d1)
    lo = min(d0, d1)

    if hi == lo:
        orders = [("H", hi, lo)]
    else:
        orders = [("H", hi, lo), ("L", lo, hi)]

    seqs = []

    for label, first_die, second_die in orders:
        first_starts = _legal_starts(st, first_die)
        for m1 in first_starts:
            s1 = _apply_single(st, first_die, m1)
            second_starts = _legal_starts(s1, second_die)

            if second_starts:
                for m2 in second_starts:
                    s2 = _apply_single(s1, second_die, m2)
                    action = "%s:%s,%s" % (label, _token(m1), _token(m2))
                    seqs.append((action, s2, (m1, m2), (first_die, second_die), label))
            else:
                action = "%s:%s,P" % (label, _token(m1))
                seqs.append((action, s1, (m1,), (first_die,), label))

    # If both dice can be played, both must be played.
    twos = [c for c in seqs if len(c[2]) == 2]
    if twos:
        return _dedupe(twos)

    ones = [c for c in seqs if len(c[2]) == 1]
    if not ones:
        return [_pass_candidate(st)]

    # If only one die can be played, the higher die must be used when possible.
    if hi != lo:
        high_possible = bool(_legal_starts(st, hi))
        if high_possible:
            filtered = [c for c in ones if c[4] == "H"]
        else:
            filtered = [c for c in ones if c[4] == "L"]
        if filtered:
            ones = filtered

    return _dedupe(ones)


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def _my_pips(st):
    return sum((i + 1) * n for i, n in enumerate(st["my_pts"])) + 25 * st["my_bar"]


def _opp_pips(st):
    return sum((24 - i) * n for i, n in enumerate(st["opp_pts"])) + 25 * st["opp_bar"]


def _has_contact(st):
    if st["my_bar"] > 0 or st["opp_bar"] > 0:
        return True

    max_my = -1
    min_opp = 24

    for i, n in enumerate(st["my_pts"]):
        if n > 0:
            max_my = i
    for i, n in enumerate(st["opp_pts"]):
        if n > 0:
            min_opp = i
            break

    if max_my < 0 or min_opp > 23:
        return False
    return max_my > min_opp


def _evaluate(st):
    if st["my_off"] >= 15:
        return 1e9
    if st["opp_off"] >= 15:
        return -1e9

    my_pip = _my_pips(st)
    opp_pip = _opp_pips(st)
    lead = opp_pip - my_pip
    contact = _has_contact(st)

    score = 0.0

    # Race equity: larger when there is no contact.
    score += (2.25 if not contact else 1.20) * lead

    # Borne-off checkers matter beyond pip count near the end.
    score += 13.0 * (st["my_off"] - st["opp_off"])
    if _all_in_home(st):
        score += 3.5 * st["my_off"]

    # Bar value. The pip count already helps, but tempo and containment matter.
    if contact:
        score += (42.0 if lead < 0 else 36.0) * st["opp_bar"]
        score -= (46.0 if lead >= 0 else 40.0) * st["my_bar"]
    else:
        score += 22.0 * st["opp_bar"]
        score -= 28.0 * st["my_bar"]

    score += _structure_score(st, contact, lead)

    if contact:
        own_blots = _my_blot_penalty(st)
        opp_blots = _opp_blot_opportunity(st)

        # Ahead: safety is paramount. Behind: accept more risk for shots.
        if lead > 15:
            score -= 1.25 * own_blots
            score += 0.25 * opp_blots
        elif lead < -15:
            score -= 0.85 * own_blots
            score += 0.55 * opp_blots
        else:
            score -= 1.00 * own_blots
            score += 0.40 * opp_blots

        score += _my_prime_score(st)
        score -= 0.92 * _opp_prime_score(st)

    return score


def _structure_score(st, contact, lead):
    my = st["my_pts"]
    opp = st["opp_pts"]

    score = 0.0
    home_phase = _all_in_home(st)

    my_home_made = sum(1 for i in range(6) if my[i] >= 2)
    opp_home_made = sum(1 for i in range(18, 24) if opp[i] >= 2)

    # Our home board contains opponent checkers hit to the bar.
    score += 2.1 * my_home_made * my_home_made
    score -= 1.8 * opp_home_made * opp_home_made

    if st["opp_bar"] > 0:
        score += st["opp_bar"] * (13.0 * my_home_made + 4.0 * my_home_made * my_home_made)
        if my_home_made >= 5:
            score += st["opp_bar"] * 22.0 * (my_home_made - 4)

    if st["my_bar"] > 0:
        score -= st["my_bar"] * (15.0 * opp_home_made + 5.0 * opp_home_made * opp_home_made)

    # Made points, anchors, and stack efficiency.
    for i, n in enumerate(my):
        if n >= 2:
            if i < 6:
                val = 4.0 + 0.45 * i
            elif i < 12:
                val = 3.0
            elif i < 18:
                val = 2.0
            else:
                val = 1.5
                if contact:
                    val += 3.0 if lead < 0 else 1.0
                    if lead > 20:
                        val -= 2.0
            score += val

        if n >= 4:
            extra = n - 3
            mult = 0.45 if (home_phase and i < 6) else 1.0
            score -= mult * 1.15 * extra * extra

    # Opponent made points block us; their home board blocks our re-entry.
    for i, n in enumerate(opp):
        if n >= 2:
            if i >= 18:
                val = 4.0 + 0.45 * (23 - i)
            elif i >= 12:
                val = 3.0
            elif i >= 6:
                val = 2.0
            else:
                val = 1.8
                if contact:
                    val += 1.8
            score -= 0.85 * val

    # Escaping back checkers is more important when ahead.
    if contact:
        back_men = sum(my[18:24])
        if lead > 8:
            score -= 1.15 * back_men
        elif lead < -8:
            # When behind, anchors/back men can preserve contact.
            made_anchors = sum(1 for i in range(18, 24) if my[i] >= 2)
            score += 2.0 * made_anchors

    return score


# ---------------------------------------------------------------------------
# Tactical risk / opportunity
# ---------------------------------------------------------------------------

def _sum_ways(dist):
    # Ordered two-dice combinations with sum == dist.
    if 2 <= dist <= 7:
        return dist - 1
    if 8 <= dist <= 12:
        return 13 - dist
    return 0


def _prob_any_die(distances):
    ds = set(d for d in distances if 1 <= d <= 6)
    k = len(ds)
    if k <= 0:
        return 0.0
    return 1.0 - ((6.0 - k) / 6.0) ** 2


def _opp_hit_prob_on_my_blot(st, point):
    """
    Approximate probability opponent can hit our blot on `point` next roll.
    Opponent moves upward, from low indices to high indices.
    """
    my = st["my_pts"]
    opp = st["opp_pts"]

    direct_distances = []
    indirect_ways = 0.0

    if st["opp_bar"] > 0:
        # Opponent enters from bar on A0..A5.
        if 0 <= point <= 5:
            direct_distances.append(point + 1)

        # With exactly one on the bar, entry plus second die may hit farther.
        if st["opp_bar"] == 1:
            for entry_die in range(1, 7):
                entry = entry_die - 1
                if my[entry] >= 2:
                    continue
                second = point - entry
                if 1 <= second <= 6:
                    indirect_ways += 1.0 if entry_die == second else 2.0
    else:
        # Direct shots from board checkers.
        lo = max(0, point - 6)
        for j in range(lo, point):
            if opp[j] > 0:
                direct_distances.append(point - j)

        # Crude two-dice indirect shots.
        lo2 = max(0, point - 12)
        hi2 = max(0, point - 6)
        for j in range(lo2, hi2):
            if opp[j] > 0:
                indirect_ways += 0.35 * _sum_ways(point - j)

    prob = _prob_any_die(direct_distances)
    prob += min(0.30, 0.45 * indirect_ways / 36.0)
    return min(0.95, prob)


def _my_hit_prob_on_opp_blot(st, point):
    """
    Approximate probability we can hit an opponent blot on `point` next roll.
    We move downward, from high indices to low indices.
    """
    my = st["my_pts"]
    opp = st["opp_pts"]

    direct_distances = []
    indirect_ways = 0.0

    if st["my_bar"] > 0:
        # We enter from bar on A23..A18.
        if 18 <= point <= 23:
            direct_distances.append(24 - point)

        if st["my_bar"] == 1:
            for entry_die in range(1, 7):
                entry = 24 - entry_die
                if opp[entry] >= 2:
                    continue
                second = entry - point
                if 1 <= second <= 6:
                    indirect_ways += 1.0 if entry_die == second else 2.0
    else:
        hi = min(23, point + 6)
        for j in range(point + 1, hi + 1):
            if my[j] > 0:
                direct_distances.append(j - point)

        hi2 = min(23, point + 12)
        lo2 = min(24, point + 7)
        for j in range(lo2, hi2 + 1):
            if my[j] > 0:
                indirect_ways += 0.35 * _sum_ways(j - point)

    prob = _prob_any_die(direct_distances)
    prob += min(0.30, 0.45 * indirect_ways / 36.0)
    return min(0.95, prob)


def _my_blot_penalty(st):
    my = st["my_pts"]
    opp_home_made = sum(1 for i in range(18, 24) if st["opp_pts"][i] >= 2)

    penalty = 0.0
    for i, n in enumerate(my):
        if n != 1:
            continue

        p = _opp_hit_prob_on_my_blot(st, i)
        if p <= 0:
            continue

        # Being hit near our bear-off board is costly; being hit deep in
        # opponent's board is less costly.
        severity = 7.0 + 0.75 * (24 - i)
        if i <= 5:
            severity += 5.0
        if i >= 18:
            severity *= 0.62

        severity += 1.15 * opp_home_made
        penalty += p * severity

    return penalty


def _opp_blot_opportunity(st):
    opp = st["opp_pts"]
    my_home_made = sum(1 for i in range(6) if st["my_pts"][i] >= 2)

    value = 0.0
    for i, n in enumerate(opp):
        if n != 1:
            continue

        p = _my_hit_prob_on_opp_blot(st, i)
        if p <= 0:
            continue

        # Hitting an advanced opponent checker costs them many pips.
        severity = 7.0 + 0.75 * (i + 1)
        severity += 0.85 * my_home_made
        value += p * severity

    return value


# ---------------------------------------------------------------------------
# Prime evaluation
# ---------------------------------------------------------------------------

def _my_prime_score(st):
    my = st["my_pts"]
    opp = st["opp_pts"]
    score = 0.0

    i = 0
    while i < 24:
        if my[i] < 2:
            i += 1
            continue

        start = i
        while i < 24 and my[i] >= 2:
            i += 1
        end = i
        length = end - start

        if length >= 2:
            trapped = st["opp_bar"] + sum(opp[:start])
            base = 2.0 * length * length
            if length >= 5:
                base += 10.0
            if length >= 6:
                base += 25.0
            mult = 0.35 + min(1.4, trapped / 5.0)
            score += base * mult

    return score


def _opp_prime_score(st):
    my = st["my_pts"]
    opp = st["opp_pts"]
    score = 0.0

    i = 0
    while i < 24:
        if opp[i] < 2:
            i += 1
            continue

        start = i
        while i < 24 and opp[i] >= 2:
            i += 1
        end = i
        length = end - start

        if length >= 2:
            trapped = st["my_bar"] + sum(my[end:])
            base = 2.0 * length * length
            if length >= 5:
                base += 10.0
            if length >= 6:
                base += 25.0
            mult = 0.35 + min(1.4, trapped / 5.0)
            score += base * mult

    return score


def _candidate_bonus(before_state, cand):
    """
    Small tie-breakers. Main legality and positional quality come from the
    generator/evaluator.
    """
    action, after, moves, dice_used, order = cand

    try:
        before_opp_bar = int(before_state.get("opp_bar", 0))
        before_my_off = int(before_state.get("my_off", 0))
    except Exception:
        before_opp_bar = 0
        before_my_off = 0

    bonus = 0.0
    bonus += 0.01 * len(moves)
    bonus += 2.5 * (after["opp_bar"] - before_opp_bar)
    bonus += 3.0 * (after["my_off"] - before_my_off)

    # Deterministic microscopic preference for using larger total pips when
    # otherwise exactly tied.
    bonus += 0.001 * sum(dice_used)

    return bonus
