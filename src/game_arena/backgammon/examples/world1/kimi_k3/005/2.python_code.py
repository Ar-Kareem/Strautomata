
"""
Backgammon arena policy.

Strategy:
  * Exact legal move generation: bar-first rule, point blocking, hitting,
    bearing-off rules (exact roll or highest occupied point), forced maximum
    dice usage, and the must-play-higher-die rule. Both dice orders are
    searched so order-dependent legality is handled.
  * One-ply search over all legal move sequences.
  * Handcrafted linear evaluation of the resulting position:
      - pip-count race term, checkers borne off, checkers on the bar
      - made points, home-board points, anchors, key points (own 5-point,
        bar point, golden anchor), primes, stacking wastage
      - blot exposure using exact direct-shot probabilities (incl. bar entry)
      - home-board pressure while the opponent is on the bar
"""

# ---------------------------------------------------------------------------
# 16: scouting notes baked into the evaluator
#   * hitting a blot is worth roughly (bar penalty + pip setback)
#   * own 5-point / bar point are the most valuable points to make
#   * a prime in front of enemy back checkers is crushing
#   * never volunteer home-board blots while the opponent is on the bar
# ---------------------------------------------------------------------------

MY_KEY = [0.0] * 24
MY_KEY[4] = 1.3    # own 5-point
MY_KEY[5] = 0.9    # own 6-point
MY_KEY[6] = 0.6    # own bar point
MY_KEY[7] = 0.4    # own 8-point
MY_KEY[19] = 0.6   # golden anchor (opponent 5-point)
MY_KEY[20] = 0.5   # anchor on opponent 4-point
OPP_KEY = [0.0] * 24
for _i in range(24):
    OPP_KEY[_i] = MY_KEY[23 - _i]

_INV36 = 1.0 / 36.0


def _gen_moves(my_pts, opp_pts, my_bar, die):
    """Legal starting points for a single checker move with one die."""
    if my_bar > 0:
        d = 24 - die
        if opp_pts[d] < 2:
            return ('B',)
        return ()
    moves = []
    ap = moves.append
    all_home = True
    for i in range(6, 24):
        if my_pts[i]:
            all_home = False
            break
    for i in range(23, -1, -1):
        if my_pts[i] == 0:
            continue
        dest = i - die
        if dest >= 0:
            if opp_pts[dest] < 2:
                ap(i)
        elif all_home:
            if dest == -1:
                ap(i)  # exact bear-off
            else:
                ok = True
                for j in range(i + 1, 6):
                    if my_pts[j]:
                        ok = False
                        break
                if ok:
                    ap(i)  # oversized roll: only from highest occupied point
    return moves


def _apply(my_pts, opp_pts, my_bar, opp_bar, my_off, mv, die):
    mp = my_pts[:]
    op = opp_pts[:]
    if mv == 'B':
        my_bar -= 1
        dest = 24 - die
    else:
        mp[mv] -= 1
        dest = mv - die
    if dest < 0:
        my_off += 1
    else:
        if op[dest] == 1:
            op[dest] = 0
            opp_bar += 1
        mp[dest] += 1
    return (mp, op, my_bar, opp_bar, my_off)


def _side_mine(pts, epts, ebar):
    """Structural score for my side (I move 23 -> 0, home is 0..5)."""
    s = 0.0
    run = 0
    KEY = MY_KEY
    for i in range(24):
        n = pts[i]
        if n >= 2:
            s += 2.0 + KEY[i]
            if i < 6:
                s += 2.5        # home-board point
            elif i >= 18:
                s += 1.5        # anchor in enemy home
            if run:
                s += 1.2        # extends a prime
            run = 1
            if n > 4:
                s -= 0.8 * (n - 4)
        else:
            run = 0
            if n == 1:
                D = 0
                mask = 0
                lo = i - 6
                if lo < 0:
                    lo = 0
                for j in range(lo, i):
                    if epts[j]:
                        d = i - j
                        if not (mask >> d) & 1:
                            mask |= 1 << d
                            D += 1
                if ebar and i < 6:
                    d = i + 1
                    if not (mask >> d) & 1:
                        D += 1
                if D:
                    p = 1.0 - (6 - D) * (6 - D) * _INV36
                    s -= 0.5 + p * (25.0 + 0.6 * (i + 1))
                else:
                    s -= 0.5
    return s


def _side_opp(pts, epts, ebar):
    """Structural score for the opponent (moves 0 -> 23, home is 18..23)."""
    s = 0.0
    run = 0
    KEY = OPP_KEY
    for i in range(24):
        n = pts[i]
        if n >= 2:
            s += 2.0 + KEY[i]
            if i >= 18:
                s += 2.5
            elif i < 6:
                s += 1.5
            if run:
                s += 1.2
            run = 1
            if n > 4:
                s -= 0.8 * (n - 4)
        else:
            run = 0
            if n == 1:
                D = 0
                mask = 0
                hi = i + 7
                if hi > 24:
                    hi = 24
                for j in range(i + 1, hi):
                    if epts[j]:
                        d = j - i
                        if not (mask >> d) & 1:
                            mask |= 1 << d
                            D += 1
                if ebar and i >= 18:
                    d = 24 - i
                    if not (mask >> d) & 1:
                        D += 1
                if D:
                    p = 1.0 - (6 - D) * (6 - D) * _INV36
                    s -= 0.5 + p * (25.0 + 0.6 * (24 - i))
                else:
                    s -= 0.5
    return s


def _eval(mp, op, mb, ob, mo, oo):
    if mo >= 15:
        return 1e18
    if oo >= 15:
        return -1e18
    mypip = 25 * mb
    oppip = 25 * ob
    for i in range(24):
        a = mp[i]
        b = op[i]
        if a:
            mypip += (i + 1) * a
        if b:
            oppip += (24 - i) * b
    sc = 0.6 * (oppip - mypip) + 15.0 * (mo - oo) + 25.0 * (ob - mb)
    sc += _side_mine(mp, op, ob)
    sc -= _side_opp(op, mp, mb)
    hm = 0
    for i in range(6):
        if mp[i] >= 2:
            hm += 1
    ho = 0
    for i in range(18, 24):
        if op[i] >= 2:
            ho += 1
    sc += 0.8 * (hm * ob - ho * mb)
    return sc


def policy(state):
    dice = state.get('dice') or []
    mp = state['my_pts']
    op = state['opp_pts']
    mb = state.get('my_bar', 0)
    ob = state.get('opp_bar', 0)
    mo = state.get('my_off', 0)
    oo = state.get('opp_off', 0)

    if len(dice) == 0:
        return "H:P,P"
    if len(dice) == 1:
        orders = ((dice[0],),)
    elif dice[0] == dice[1]:
        orders = ((dice[0], dice[1]),)
    else:
        orders = ((dice[0], dice[1]), (dice[1], dice[0]))

    cand = []
    ac = cand.append
    for order in orders:
        d1 = order[0]
        m1s = _gen_moves(mp, op, mb, d1)
        if m1s:
            two = len(order) > 1
            for m1 in m1s:
                st1 = _apply(mp, op, mb, ob, mo, m1, d1)
                if two:
                    d2 = order[1]
                    m2s = _gen_moves(st1[0], st1[1], st1[2], d2)
                    if m2s:
                        for m2 in m2s:
                            st2 = _apply(st1[0], st1[1], st1[2], st1[3],
                                         st1[4], m2, d2)
                            ac((((m1, d1), (m2, d2)), st2))
                        continue
                ac((((m1, d1),), st1))
        elif len(order) > 1:
            d2 = order[1]
            for m2 in _gen_moves(mp, op, mb, d2):
                st2 = _apply(mp, op, mb, ob, mo, m2, d2)
                ac((((m2, d2),), st2))

    if not cand:
        return "H:P,P"

    # Rule: use the maximum number of dice possible.
    maxn = 1
    for moves, st in cand:
        if len(moves) > maxn:
            maxn = len(moves)
    if maxn == 2:
        cand = [c for c in cand if len(c[0]) == 2]
    elif len(dice) == 2 and dice[0] != dice[1]:
        # Rule: if only one die can be played, prefer the higher one.
        hi = dice[0] if dice[0] > dice[1] else dice[1]
        hic = [c for c in cand if c[0][0][1] == hi]
        if hic:
            cand = hic

    # Deduplicate identical end positions.
    uniq = {}
    for moves, st in cand:
        key = (tuple(st[0]), tuple(st[1]), st[2], st[3], st[4])
        if key not in uniq:
            uniq[key] = (moves, st)

    best = None
    bestv = -1e30
    for moves, st in uniq.values():
        v = _eval(st[0], st[1], st[2], st[3], st[4], oo)
        if v > bestv:
            bestv = v
            best = moves

    if best is None:
        return "H:P,P"

    if len(dice) == 2 and dice[0] != dice[1]:
        hi = dice[0] if dice[0] > dice[1] else dice[1]
        oc = 'H' if best[0][1] == hi else 'L'
    else:
        oc = 'H'
    f1 = best[0][0]
    t1 = 'B' if f1 == 'B' else 'A%d' % f1
    if len(best) > 1:
        f2 = best[1][0]
        t2 = 'B' if f2 == 'B' else 'A%d' % f2
    else:
        t2 = 'P'
    return oc + ':' + t1 + ',' + t2
