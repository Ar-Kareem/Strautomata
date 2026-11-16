
# backgammon_policy.py

from itertools import product

def policy(state: dict) -> str:
    """
    Return a legal move string in format <ORDER>:<FROM1>,<FROM2>.
    The player to move always moves from high indices toward low indices.
    """

    dice = list(state.get("dice", []))
    if not dice:
        return "H:P,P"

    my_pts = list(state.get("my_pts", [0] * 24))
    opp_pts = list(state.get("opp_pts", [0] * 24))
    my_bar = int(state.get("my_bar", 0))
    opp_bar = int(state.get("opp_bar", 0))
    my_off = int(state.get("my_off", 0))
    opp_off = int(state.get("opp_off", 0))

    if len(dice) == 1:
        d = dice[0]
        actions = _legal_sequences(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, [d])
        if not actions:
            return "H:P,P"
        best = max(actions, key=lambda a: _eval(a[5], a[6], a[7], a[8], a[9], a[10], state))
        frm = best[1][0] if best[1] else "P"
        return "H:%s,P" % frm

    d1, d2 = dice[0], dice[1]
    hi, lo = max(d1, d2), min(d1, d2)

    # Backgammon usually has four moves on doubles, but the arena format supports up to two.
    # We therefore encode two moves using equal dice.
    if hi == lo:
        actions = _legal_sequences(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, [hi, lo])
        if not actions:
            return "H:P,P"
        best = max(actions, key=lambda a: _eval(a[5], a[6], a[7], a[8], a[9], a[10], state))
        f1 = best[1][0] if len(best[1]) > 0 else "P"
        f2 = best[1][1] if len(best[1]) > 1 else "P"
        return "H:%s,%s" % (f1, f2)

    cand = []

    acts_h = _legal_sequences(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, [hi, lo])
    for a in acts_h:
        cand.append(("H", a))

    acts_l = _legal_sequences(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, [lo, hi])
    for a in acts_l:
        cand.append(("L", a))

    if not cand:
        return "H:P,P"

    # Enforce standard constraints across die orders.
    max_len = max(len(a[1][1]) for a in cand)
    cand = [a for a in cand if len(a[1][1]) == max_len]

    if max_len == 1:
        # If only one die can be played, higher die must be played when possible.
        high_play = [a for a in cand if a[1][2] and a[1][2][0] == hi]
        if high_play:
            cand = high_play

    best_order, best = max(
        cand,
        key=lambda oa: _eval(oa[1][5], oa[1][6], oa[1][7], oa[1][8], oa[1][9], oa[1][10], state)
    )

    f1 = best[1][0] if len(best[1]) > 0 else "P"
    f2 = best[1][1] if len(best[1]) > 1 else "P"
    return "%s:%s,%s" % (best_order, f1, f2)


def _all_home(my_pts, my_bar):
    if my_bar > 0:
        return False
    for i in range(6, 24):
        if my_pts[i] > 0:
            return False
    return True


def _can_bear_from(my_pts, src, die):
    dest = src - die
    if dest == -1:
        return True
    if dest < -1:
        # Can bear off from a lower die only if no checker is on a higher point.
        for j in range(src + 1, 6):
            if my_pts[j] > 0:
                return False
        return True
    return False


def _single_moves(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, die):
    moves = []

    if my_bar > 0:
        dest = 24 - die
        if 0 <= dest < 24 and opp_pts[dest] < 2:
            moves.append(("B", dest, False))
        return moves

    home = _all_home(my_pts, my_bar)

    for src in range(24):
        if my_pts[src] <= 0:
            continue
        dest = src - die
        if dest >= 0:
            if opp_pts[dest] < 2:
                moves.append(("A%d" % src, dest, False))
        else:
            if home and src < 6 and _can_bear_from(my_pts, src, die):
                moves.append(("A%d" % src, -1, True))

    return moves


def _apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, move):
    frm, dest, bear = move

    my_pts = my_pts[:]
    opp_pts = opp_pts[:]

    if frm == "B":
        my_bar -= 1
    else:
        src = int(frm[1:])
        my_pts[src] -= 1

    hit = False
    if bear:
        my_off += 1
    else:
        if opp_pts[dest] == 1:
            opp_pts[dest] = 0
            opp_bar += 1
            hit = True
        my_pts[dest] += 1

    return my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, hit


def _legal_sequences(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, dice_order):
    results = []

    def rec(k, pts, opts, bar, obar, off, ooff, froms, used, hits):
        if k >= len(dice_order):
            results.append((None, froms[:], used[:], hits[:], None, pts, opts, bar, obar, off, ooff))
            return
        die = dice_order[k]
        moves = _single_moves(pts, opts, bar, obar, off, ooff, die)
        if not moves:
            results.append((None, froms[:], used[:], hits[:], None, pts, opts, bar, obar, off, ooff))
            return
        for mv in moves:
            npts, nopts, nbar, nobar, noff, nooff, hit = _apply_move(
                pts, opts, bar, obar, off, ooff, mv
            )
            rec(k + 1, npts, nopts, nbar, nobar, noff, nooff,
                froms + [mv[0]], used + [die], hits + [hit])

    rec(0, my_pts[:], opp_pts[:], my_bar, opp_bar, my_off, opp_off, [], [], [])
    return results


def _pip_my(my_pts, my_bar):
    # Distance to bear off from point i is i+1; bar roughly 25 pips.
    return sum(my_pts[i] * (i + 1) for i in range(24)) + my_bar * 25


def _pip_opp(opp_pts, opp_bar):
    # Opponent moves opposite direction; distance to bear off is 24-i.
    return sum(opp_pts[i] * (24 - i) for i in range(24)) + opp_bar * 25


def _eval(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, orig_state):
    my_pip = _pip_my(my_pts, my_bar)
    opp_pip = _pip_opp(opp_pts, opp_bar)

    score = 0.0

    # Winning / race fundamentals.
    score += my_off * 1200.0
    score -= opp_off * 900.0
    score -= my_bar * 650.0
    score += opp_bar * 520.0
    score += (opp_pip - my_pip) * 8.0

    # Made points and blots.
    made = 0
    blots = 0
    anchors = 0
    builders = 0

    for i, n in enumerate(my_pts):
        if n >= 2:
            made += 1
            # Home-board points are especially valuable.
            if i <= 5:
                score += 95.0 + (6 - i) * 8.0
            elif i <= 11:
                score += 45.0
            else:
                score += 22.0
            if n > 3:
                score -= (n - 3) * 10.0
        elif n == 1:
            blots += 1
            danger = _hit_danger(i, opp_pts, opp_bar)
            score -= 18.0 + 28.0 * danger
        if n >= 2 and i >= 18:
            anchors += 1
            score += 45.0
        if n == 3:
            builders += 1
            score += 8.0

    # Prime-like consecutive made points.
    run = 0
    best_run = 0
    for i in range(24):
        if my_pts[i] >= 2:
            run += 1
            best_run = max(best_run, run)
        else:
            run = 0
    score += best_run * best_run * 18.0

    # Opponent made home board is bad for us if we may be hit.
    opp_home_strength = sum(1 for i in range(18, 24) if opp_pts[i] >= 2)
    if my_bar or blots:
        score -= opp_home_strength * 45.0

    # Prefer hitting, especially when our home board is strong.
    old_opp_bar = int(orig_state.get("opp_bar", 0))
    score += max(0, opp_bar - old_opp_bar) * (260.0 + 35.0 * sum(1 for i in range(6) if my_pts[i] >= 2))

    # Encourage bearing in/off and avoid stragglers in race.
    furthest = -1
    for i in range(23, -1, -1):
        if my_pts[i]:
            furthest = i
            break
    if furthest >= 0:
        score -= furthest * 3.5

    if _all_home(my_pts, my_bar):
        # In bearoff, pure pip/off count dominates; avoid gaps mildly.
        score += 350.0
        for i in range(6):
            if my_pts[i] == 0:
                score -= 3.0
            else:
                score += (6 - i) * my_pts[i] * 2.0

    # Do not over-penalize blots when far behind: contact can be necessary.
    if my_pip > opp_pip + 30:
        score += anchors * 35.0
        score -= blots * 4.0

    return score


def _hit_danger(pos, opp_pts, opp_bar):
    """
    Approximate probability-like exposure count. Opponent moves upward, so an
    opposing checker behind our blot is at lower index and can hit with distance pos-j.
    Opponent bar enters at our point die-1 in absolute coordinates.
    """
    danger = 0.0

    if opp_bar > 0:
        entry_die = pos + 1
        if 1 <= entry_die <= 6:
            danger += 1.5

    for j in range(max(0, pos - 6), pos):
        if opp_pts[j] > 0:
            dist = pos - j
            if 1 <= dist <= 6:
                danger += min(2, opp_pts[j]) * _die_weight(dist)

    # Combination-shot roughness.
    for j in range(max(0, pos - 12), pos - 6):
        if opp_pts[j] > 0:
            danger += 0.15 * min(2, opp_pts[j])

    return danger


def _die_weight(d):
    # Relative frequency/utility of direct shots.
    if d in (1, 2, 3, 4, 5, 6):
        return {1: 1.0, 2: 0.95, 3: 0.9, 4: 0.85, 5: 0.8, 6: 0.75}[d]
    return 0.0
