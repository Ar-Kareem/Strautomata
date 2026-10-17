
# backgammon_policy.py
# Implements: policy(state: dict) -> str

from itertools import product

def _dest_from(src, die):
    """Our checkers move from high indices toward low indices. src None means bar."""
    if src is None:
        # Entering from bar: die 1 enters A23, die 6 enters A18.
        return 24 - die
    return src - die

def _all_in_home(my_pts, my_bar):
    if my_bar > 0:
        return False
    return sum(my_pts[6:24]) == 0

def _can_bear_from(src, die, my_pts, my_bar):
    if not _all_in_home(my_pts, my_bar):
        return False
    dest = src - die
    if dest >= 0:
        return False
    # Exact bear-off is always okay.
    if dest == -1:
        return True
    # Oversized die may bear off only from highest occupied point among home checkers.
    # Since we move toward 0, "higher" point is farther from bearing off.
    for p in range(src + 1, 6):
        if my_pts[p] > 0:
            return False
    return True

def _single_moves(pos, die):
    """Return legal starts for one die in current mutable/copy position.
    Start is None for bar, or point index 0..23.
    """
    my_pts, opp_pts, my_bar = pos["my_pts"], pos["opp_pts"], pos["my_bar"]
    moves = []
    if my_bar > 0:
        d = _dest_from(None, die)
        if 0 <= d < 24 and opp_pts[d] < 2:
            moves.append(None)
        return moves

    home = _all_in_home(my_pts, my_bar)
    for src in range(24):
        if my_pts[src] <= 0:
            continue
        d = _dest_from(src, die)
        if 0 <= d < 24:
            if opp_pts[d] < 2:
                moves.append(src)
        else:
            if home and _can_bear_from(src, die, my_pts, my_bar):
                moves.append(src)
    return moves

def _apply_single(pos, start, die):
    """Apply one legal checker move to a copied position."""
    my_pts, opp_pts = pos["my_pts"], pos["opp_pts"]

    if start is None:
        pos["my_bar"] -= 1
    else:
        my_pts[start] -= 1

    d = _dest_from(start, die)

    if d < 0:
        pos["my_off"] += 1
        return

    # Hit blot.
    if opp_pts[d] == 1:
        opp_pts[d] = 0
        pos["opp_bar"] += 1
    my_pts[d] += 1

def _copy_pos(state):
    return {
        "my_pts": list(state["my_pts"]),
        "opp_pts": list(state["opp_pts"]),
        "my_bar": int(state["my_bar"]),
        "opp_bar": int(state["opp_bar"]),
        "my_off": int(state["my_off"]),
        "opp_off": int(state["opp_off"]),
    }

def _tok(start):
    return "B" if start is None else ("A%d" % start)

def _pip_count(my_pts, my_bar):
    # Distance to bear off for our side: point i needs i+1 pips. Bar roughly 25.
    return sum((i + 1) * c for i, c in enumerate(my_pts)) + 25 * my_bar

def _opp_pip_count(opp_pts, opp_bar):
    # Opponent moves low to high; distance from point i to off is 24-i.
    return sum((24 - i) * c for i, c in enumerate(opp_pts)) + 25 * opp_bar

def _hit_chance_penalty(my_pts, opp_pts):
    """Approximate risk of our blots being hit by opponent next turn."""
    pen = 0.0
    blots = [i for i, c in enumerate(my_pts) if c == 1]
    opp_occupied = [i for i, c in enumerate(opp_pts) if c > 0]
    for b in blots:
        # Opponent moves upward, can hit from b-die.
        risk = 0
        for die in range(1, 7):
            s = b - die
            if 0 <= s < 24 and opp_pts[s] > 0:
                risk += 1
        # Extra risk for direct shots from multiple men.
        men_attack = sum(opp_pts[b-d] for d in range(1, 7) if 0 <= b-d < 24)
        # Blots in our outer/back boards are usually more costly.
        value = 1.0 + (b / 23.0)
        pen += value * (risk * 4.0 + men_attack * 1.5)
    return pen

def _made_points_score(my_pts):
    score = 0.0
    for i, c in enumerate(my_pts):
        if c >= 2:
            # Home-board points are very valuable; high anchors also useful.
            if 0 <= i <= 5:
                score += 18.0 + (5 - i) * 1.5
            elif 18 <= i <= 23:
                score += 8.0
            else:
                score += 5.0
            if c > 2:
                score -= (c - 2) * 1.2  # avoid excessive stacks
        elif c == 1:
            score -= 2.0
    return score

def _prime_score(my_pts):
    # Reward consecutive made points.
    best = 0
    cur = 0
    total = 0.0
    for i in range(24):
        if my_pts[i] >= 2:
            cur += 1
            best = max(best, cur)
            total += cur * 1.5
        else:
            cur = 0
    return total + best * best * 2.0

def _escape_score(my_pts):
    # Penalize checkers left farthest back (high indices).
    score = 0.0
    for i in range(18, 24):
        score -= my_pts[i] * (i - 17) * 5.0
    return score

def _bearing_score(my_pts, my_off):
    s = my_off * 120.0
    # Once in home board, prefer smooth distribution near bear-off.
    if sum(my_pts[6:24]) == 0:
        for i in range(6):
            s += my_pts[i] * (6 - i) * 3.0
    return s

def _evaluate(pos):
    my_pts, opp_pts = pos["my_pts"], pos["opp_pts"]
    my_pip = _pip_count(my_pts, pos["my_bar"])
    opp_pip = _opp_pip_count(opp_pts, pos["opp_bar"])

    score = 0.0
    score += (opp_pip - my_pip) * 3.0
    score += _bearing_score(my_pts, pos["my_off"])
    score -= pos["opp_off"] * 100.0

    # Bar/hit priorities.
    score += pos["opp_bar"] * 70.0
    score -= pos["my_bar"] * 95.0

    score += _made_points_score(my_pts)
    score += _prime_score(my_pts)
    score += _escape_score(my_pts)

    # Opponent made home points are dangerous / strong for them.
    for i, c in enumerate(opp_pts):
        if c >= 2:
            if 18 <= i <= 23:
                score -= 14.0
            else:
                score -= 4.0

    score -= _hit_chance_penalty(my_pts, opp_pts)

    # Prefer having builders rather than huge stacks.
    for i, c in enumerate(my_pts):
        if c >= 5:
            score -= (c - 4) * 6.0

    return score

def _legal_sequences_for_order(state, dice_order, order_char):
    """Generate legal sequences for a two-die non-double roll in a given order."""
    initial = _copy_pos(state)
    d1, d2 = dice_order

    firsts = _single_moves(initial, d1)
    seqs = []

    if firsts:
        for s1 in firsts:
            p1 = _copy_pos(initial)
            _apply_single(p1, s1, d1)
            seconds = _single_moves(p1, d2)
            if seconds:
                for s2 in seconds:
                    p2 = _copy_pos(p1)
                    _apply_single(p2, s2, d2)
                    seqs.append((order_char, s1, s2, p2, 2))
            else:
                seqs.append((order_char, s1, "P", p1, 1))
    else:
        # First die in this order cannot be played; maybe second die can.
        seconds = _single_moves(initial, d2)
        if seconds:
            for s2 in seconds:
                p2 = _copy_pos(initial)
                _apply_single(p2, s2, d2)
                # Encoded first FROM is P, second move uses second die.
                seqs.append((order_char, "P", s2, p2, 1))
        else:
            seqs.append((order_char, "P", "P", initial, 0))
    return seqs

def _generate_legal_actions(state):
    dice = list(state.get("dice", []))
    if len(dice) == 0:
        return [("H", "P", "P", _copy_pos(state), 0)]
    if len(dice) == 1:
        d = dice[0]
        pos = _copy_pos(state)
        moves = _single_moves(pos, d)
        out = []
        if moves:
            for s in moves:
                p = _copy_pos(pos)
                _apply_single(p, s, d)
                out.append(("H", s, "P", p, 1))
        else:
            out.append(("H", "P", "P", pos, 0))
        return out

    a, b = dice[0], dice[1]

    # Arena format only supports two checker moves, so doubles are treated as two same-die moves
    # if they appear here.
    if a == b:
        seqs = _legal_sequences_for_order(state, (a, b), "H")
        max_used = max(x[4] for x in seqs)
        return [x for x in seqs if x[4] == max_used]

    hi, lo = max(a, b), min(a, b)
    seqs = []
    seqs.extend(_legal_sequences_for_order(state, (hi, lo), "H"))
    seqs.extend(_legal_sequences_for_order(state, (lo, hi), "L"))

    # Enforce "if both dice can be played, play both"; otherwise play one die.
    max_used = max(x[4] for x in seqs)

    filtered = [x for x in seqs if x[4] == max_used]

    # If only one die can be played, must play higher die when possible.
    if max_used == 1:
        high_playable = []
        for x in filtered:
            order, s1, s2, p, used = x
            if order == "H" and s1 != "P":
                high_playable.append(x)
            if order == "L" and s2 != "P":
                high_playable.append(x)
        if high_playable:
            filtered = high_playable

    return filtered

def _format_action(action):
    order, s1, s2, _pos, _used = action
    f1 = "P" if s1 == "P" else _tok(s1)
    f2 = "P" if s2 == "P" else _tok(s2)
    return "%s:%s,%s" % (order, f1, f2)

def policy(state: dict) -> str:
    try:
        actions = _generate_legal_actions(state)
        if not actions:
            return "H:P,P"
        best = None
        best_score = -10**100
        for a in actions:
            sc = _evaluate(a[3])
            # Small tie-breakers: prefer using more dice, prefer H for consistency.
            sc += a[4] * 10000.0
            if a[0] == "H":
                sc += 0.01
            if sc > best_score:
                best_score = sc
                best = a
        return _format_action(best)
    except Exception:
        # Extremely conservative syntactically valid fallback. Usually legal only if no moves,
        # but prevents crashes; normal path above is designed to return legal actions.
        return "H:P,P"
