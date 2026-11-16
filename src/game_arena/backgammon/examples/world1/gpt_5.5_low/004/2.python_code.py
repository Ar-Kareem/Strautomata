
# backgammon_policy.py

def policy(state: dict) -> str:
    """
    Return a legal move string in the required format:
        <ORDER>:<FROM1>,<FROM2>

    The policy enumerates legal candidate moves for both die orders and
    evaluates the resulting positions with a practical heuristic.
    """

    dice = list(state.get("dice", []))
    if len(dice) == 0:
        return "H:P,P"

    if len(dice) == 1:
        dice = [dice[0], dice[0]]

    d1, d2 = dice[0], dice[1]
    hi, lo = max(d1, d2), min(d1, d2)

    candidates = []

    # Generate candidates for both order encodings.
    for order, ordered_dice in (("H", [hi, lo]), ("L", [lo, hi])):
        seqs = _generate_sequences(state, ordered_dice)
        for starts, end_state, used_values in seqs:
            candidates.append((order, starts, end_state, used_values))

    if not candidates:
        return "H:P,P"

    # Enforce maximum number of dice played.
    max_used = max(len(c[3]) for c in candidates)
    candidates = [c for c in candidates if len(c[3]) == max_used]

    # If only one die can be played, the higher die must be used when possible.
    if max_used == 1:
        high_candidates = [c for c in candidates if c[3] and c[3][0] == hi]
        if high_candidates:
            candidates = high_candidates

    if not candidates:
        return "H:P,P"

    # Select best heuristic result.
    best = None
    best_score = None
    for cand in candidates:
        order, starts, end_state, used_values = cand
        score = _evaluate(end_state)
        if best is None or score > best_score:
            best = cand
            best_score = score

    order, starts, end_state, used_values = best
    s1 = _fmt_start(starts[0])
    s2 = _fmt_start(starts[1])
    return f"{order}:{s1},{s2}"


def _copy_state(state):
    return {
        "my_pts": list(state.get("my_pts", [0] * 24)),
        "opp_pts": list(state.get("opp_pts", [0] * 24)),
        "my_bar": int(state.get("my_bar", 0)),
        "opp_bar": int(state.get("opp_bar", 0)),
        "my_off": int(state.get("my_off", 0)),
        "opp_off": int(state.get("opp_off", 0)),
        "dice": list(state.get("dice", [])),
    }


def _generate_sequences(state, ordered_dice):
    """
    Generate legal two-step sequences for the specified dice order.
    Returns tuples:
        (starts, resulting_state, used_die_values)
    starts is always length 2, using "P" for pass.
    """
    base = _copy_state(state)
    results = []

    first_die = ordered_dice[0]
    first_moves = _legal_single_moves(base, first_die)

    if not first_moves:
        # First die cannot be played.
        second_die = ordered_dice[1]
        second_moves = _legal_single_moves(base, second_die)
        if not second_moves:
            results.append((["P", "P"], base, []))
        else:
            for start2 in second_moves:
                st2 = _apply_move(base, start2, second_die)
                results.append((["P", start2], st2, [second_die]))
        return results

    for start1 in first_moves:
        st1 = _apply_move(base, start1, first_die)
        second_die = ordered_dice[1]
        second_moves = _legal_single_moves(st1, second_die)

        if not second_moves:
            results.append(([start1, "P"], st1, [first_die]))
        else:
            for start2 in second_moves:
                st2 = _apply_move(st1, start2, second_die)
                results.append(([start1, start2], st2, [first_die, second_die]))

    return results


def _legal_single_moves(st, die):
    """
    Return legal starting locations for a single checker move using die.
    Starts are either "B" or integer point indices 0..23.
    """
    my_pts = st["my_pts"]
    opp_pts = st["opp_pts"]

    # Bar checkers must enter first.
    if st["my_bar"] > 0:
        dest = 24 - die
        if 0 <= dest <= 23 and opp_pts[dest] < 2:
            return ["B"]
        return []

    moves = []

    all_home = _all_in_home(st)

    for src in range(24):
        if my_pts[src] <= 0:
            continue

        dest = src - die

        if dest >= 0:
            if opp_pts[dest] < 2:
                moves.append(src)
        else:
            # Bearing off.
            if all_home and _can_bear_off_from(my_pts, src, die):
                moves.append(src)

    return moves


def _all_in_home(st):
    if st["my_bar"] > 0:
        return False
    # Player moves from 23 down to 0, so home board is points 0..5.
    for i in range(6, 24):
        if st["my_pts"][i] > 0:
            return False
    return True


def _can_bear_off_from(my_pts, src, die):
    # Exact bearoff.
    if die == src + 1:
        return True

    # Oversized die can bear off only from the highest occupied point.
    if die > src + 1:
        for higher in range(src + 1, 6):
            if my_pts[higher] > 0:
                return False
        return True

    return False


def _apply_move(st, start, die):
    """
    Apply one legal move and return a copied resulting state.
    """
    ns = _copy_state(st)
    my_pts = ns["my_pts"]
    opp_pts = ns["opp_pts"]

    if start == "P":
        return ns

    if start == "B":
        ns["my_bar"] -= 1
        dest = 24 - die
    else:
        src = int(start)
        my_pts[src] -= 1
        dest = src - die

    if dest < 0:
        ns["my_off"] += 1
        return ns

    # Hit opponent blot.
    if opp_pts[dest] == 1:
        opp_pts[dest] = 0
        ns["opp_bar"] += 1

    my_pts[dest] += 1
    return ns


def _fmt_start(start):
    if start == "P":
        return "P"
    if start == "B":
        return "B"
    return "A" + str(int(start))


def _evaluate(st):
    """
    Heuristic evaluator from our perspective. Larger is better.
    """
    my_pts = st["my_pts"]
    opp_pts = st["opp_pts"]

    score = 0.0

    # Winning race / bearing off.
    score += 120.0 * st["my_off"]
    score -= 120.0 * st["opp_off"]

    my_pips = _pip_count_my(my_pts, st["my_bar"])
    opp_pips = _pip_count_opp(opp_pts, st["opp_bar"])
    score += 2.2 * (opp_pips - my_pips)

    # Opponent on bar is very valuable, especially with a closed/strong home board.
    home_strength = 0
    for i in range(0, 6):
        if my_pts[i] >= 2:
            home_strength += 1
    score += 30.0 * st["opp_bar"]
    score += 7.0 * st["opp_bar"] * home_strength

    # Our own bar is bad.
    score -= 35.0 * st["my_bar"]

    # Made points.
    for i in range(24):
        if my_pts[i] >= 2:
            score += 5.0
            if i <= 5:
                score += 8.0
            elif i <= 11:
                score += 3.0

    # Prime-like consecutive made points.
    consec = 0
    best_consec = 0
    for i in range(23, -1, -1):
        if my_pts[i] >= 2:
            consec += 1
            if consec > best_consec:
                best_consec = consec
        else:
            consec = 0
    score += 6.0 * best_consec * best_consec

    # Penalize blots, especially those likely to be hit.
    for i in range(24):
        if my_pts[i] == 1:
            danger = _blot_danger(i, opp_pts)
            score -= 4.0
            score -= 5.0 * danger

            # Blots in our home board are less awful during bearoff but still weak.
            if i <= 5:
                score -= 1.0

    # Reward attacking opponent blots / vulnerable opponent structure.
    for i in range(24):
        if opp_pts[i] == 1:
            score += 1.5

    # Prefer compact stacks, but discourage huge overstacking.
    for i in range(24):
        if my_pts[i] > 5:
            score -= 2.0 * (my_pts[i] - 5)

    # Bearing-off phase: prioritize taking checkers off and avoiding waste.
    if _all_in_home(st):
        score += 15.0 * st["my_off"]
        for i in range(6):
            score -= 0.8 * my_pts[i] * i

    return score


def _pip_count_my(my_pts, my_bar):
    # Distance to bear off is point index + 1. Bar is roughly 25 pips.
    total = 25 * my_bar
    for i, n in enumerate(my_pts):
        total += n * (i + 1)
    return total


def _pip_count_opp(opp_pts, opp_bar):
    # Opponent moves from 0 to 23, distance to bear off is 24 - index.
    total = 25 * opp_bar
    for i, n in enumerate(opp_pts):
        total += n * (24 - i)
    return total


def _blot_danger(my_index, opp_pts):
    """
    Approximate number of ways opponent can hit this blot next turn.
    Opponent moves upward, so an opponent checker behind this point can hit
    from my_index - d for d in 1..6.
    """
    danger = 0.0

    for d in range(1, 7):
        src = my_index - d
        if 0 <= src < 24 and opp_pts[src] > 0:
            # Direct shot.
            danger += 1.0
            if opp_pts[src] >= 2:
                danger += 0.25

    # Opponent on bar can enter onto our blot only on points 0..5.
    # From opponent perspective, bar entry lands at points 0..5.
    # This state representation has opponent checkers mirrored by engine rules,
    # but a small penalty for home-board blots is handled elsewhere.
    return danger
