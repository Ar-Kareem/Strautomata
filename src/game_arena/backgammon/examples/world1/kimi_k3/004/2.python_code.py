
"""
Backgammon arena policy.

Approach:
  1. Enumerate every legal checker-move sequence for the rolled dice,
     enforcing: bar-first, blocked points, bearing-off rules, must use
     both dice when possible, must use the higher die when only one is
     playable.
  2. Score each resulting position with a linear heuristic: pip-count
     race, blot exposure (direct shots), made points, home-board
     strength, primes, anchors, stacks, bar and borne-off terms.
  3. Play the move leading to the best evaluated position.
"""


def _gen_moves(my, opp, my_bar, die):
    """Return list of legal checker moves for one die.

    A move is encoded as an int point index, or -1 for the bar.
    """
    moves = []
    if my_bar > 0:
        dest = 24 - die
        if opp[dest] < 2:
            moves.append(-1)
        return moves
    home = True
    for i in range(6, 24):
        if my[i]:
            home = False
            break
    for p in range(24):
        if my[p] == 0:
            continue
        dest = p - die
        if dest >= 0:
            if opp[dest] < 2:
                moves.append(p)
        elif home:
            if die == p + 1:
                moves.append(p)          # exact bear-off
            elif die > p + 1:            # oversize bear-off
                clear = True
                for q in range(p + 1, 6):
                    if my[q]:
                        clear = False
                        break
                if clear:
                    moves.append(p)
    return moves


def _apply(my, opp, my_bar, opp_bar, my_off, move, die):
    """Apply one checker move, returning the new position tuple."""
    my = my[:]
    opp = opp[:]
    if move == -1:
        my_bar -= 1
        dest = 24 - die
        if opp[dest] == 1:
            opp[dest] = 0
            opp_bar += 1
        my[dest] += 1
    else:
        my[move] -= 1
        dest = move - die
        if dest < 0:
            my_off += 1
        else:
            if opp[dest] == 1:
                opp[dest] = 0
                opp_bar += 1
            my[dest] += 1
    return (my, opp, my_bar, opp_bar, my_off)


def _tok(move):
    return 'B' if move == -1 else 'A' + str(move)


def _candidates(my, opp, my_bar, opp_bar, my_off, dice):
    """Generate all candidate sequences.

    Returns (cands, hi, lo); each candidate is
    (order, tok1, tok2, dice_used, used_higher_die, result_tuple).
    """
    single = len(dice) == 1
    if single:
        hi = lo = dice[0]
    else:
        hi = max(dice)
        lo = min(dice)
    if single or hi == lo:
        orders = (('H', hi, lo),)
    else:
        orders = (('H', hi, lo), ('L', lo, hi))

    cands = []
    state0 = (my, opp, my_bar, opp_bar, my_off)
    for order, d1, d2 in orders:
        moves1 = _gen_moves(my, opp, my_bar, d1)
        if not moves1:
            if single:
                cands.append((order, 'P', 'P', 0, False, state0))
                continue
            moves2 = _gen_moves(my, opp, my_bar, d2)
            if not moves2:
                cands.append((order, 'P', 'P', 0, False, state0))
            else:
                for m2 in moves2:
                    res = _apply(my, opp, my_bar, opp_bar, my_off, m2, d2)
                    cands.append((order, 'P', _tok(m2), 1, d2 == hi, res))
        else:
            for m1 in moves1:
                r1 = _apply(my, opp, my_bar, opp_bar, my_off, m1, d1)
                if single:
                    cands.append((order, _tok(m1), 'P', 1, d1 == hi, r1))
                    continue
                moves2 = _gen_moves(r1[0], r1[1], r1[2], d2)
                if not moves2:
                    cands.append((order, _tok(m1), 'P', 1, d1 == hi, r1))
                else:
                    for m2 in moves2:
                        r2 = _apply(r1[0], r1[1], r1[2], r1[3], r1[4], m2, d2)
                        cands.append((order, _tok(m1), _tok(m2), 2, True, r2))
    return cands, hi, lo


def _evaluate(my, opp, my_bar, opp_bar, my_off, opp_off):
    """Heuristic position score from our perspective (higher = better)."""
    my_pip = 25 * my_bar
    opp_pip = 25 * opp_bar
    my_pts_sc = 0.0
    opp_pts_sc = 0.0
    my_blot_sc = 0.0
    opp_blot_sc = 0.0
    run_my = 0
    run_opp = 0

    for i in range(24):
        cm = my[i]
        if cm:
            my_pip += cm * (i + 1)
            if cm == 1:
                shots = 0
                lo_i = i - 6
                if lo_i < 0:
                    lo_i = 0
                for j in range(lo_i, i):
                    if opp[j]:
                        shots += opp[j]
                if i <= 5:
                    shots += opp_bar
                my_blot_sc += (2.0 + (shots if shots < 8 else 8)) if shots else 0.4
                run_my = 0
            else:
                val = 2.0
                if i <= 5:
                    val += 2.0
                    if i == 3 or i == 4:
                        val += 0.75
                elif i >= 18:
                    val += 1.25
                run_my += 1
                if run_my >= 2:
                    val += 0.75
                if run_my >= 4:
                    val += 2.0
                if cm >= 5:
                    val -= 0.4 * (cm - 4)
                my_pts_sc += val
        else:
            run_my = 0

        co = opp[i]
        if co:
            opp_pip += co * (24 - i)
            if co == 1:
                shots = 0
                hi_i = i + 6
                if hi_i > 23:
                    hi_i = 23
                for j in range(i + 1, hi_i + 1):
                    if my[j]:
                        shots += my[j]
                if i >= 18:
                    shots += my_bar
                opp_blot_sc += (2.0 + (shots if shots < 8 else 8)) if shots else 0.4
                run_opp = 0
            else:
                val = 2.0
                if i >= 18:
                    val += 2.0
                    if i == 19 or i == 20:
                        val += 0.75
                elif i <= 5:
                    val += 1.25
                run_opp += 1
                if run_opp >= 2:
                    val += 0.75
                if run_opp >= 4:
                    val += 2.0
                if co >= 5:
                    val -= 0.4 * (co - 4)
                opp_pts_sc += val
        else:
            run_opp = 0

    score = float(opp_pip - my_pip)
    score += 12.0 * (opp_bar - my_bar)
    score += 4.0 * (my_off - opp_off)
    score += (my_pts_sc - opp_pts_sc)
    score += (opp_blot_sc - my_blot_sc)
    return score


def policy(state: dict) -> str:
    try:
        my = [int(x) for x in state['my_pts']]
        opp = [int(x) for x in state['opp_pts']]
        my_bar = int(state['my_bar'])
        opp_bar = int(state['opp_bar'])
        my_off = int(state['my_off'])
        opp_off = int(state['opp_off'])
        dice = [int(d) for d in state['dice']]

        if not dice:
            return "H:P,P"

        cands, hi, lo = _candidates(my, opp, my_bar, opp_bar, my_off, dice)
        if not cands:
            return "H:P,P"

        # Rule filters: use maximum number of dice; if only one die is
        # playable, the higher die must be used when possible.
        max_used = 0
        for c in cands:
            if c[3] > max_used:
                max_used = c[3]
        pool = [c for c in cands if c[3] == max_used]
        if max_used == 1 and hi != lo:
            hipool = [c for c in pool if c[4]]
            if hipool:
                pool = hipool

        best = pool[0]
        try:
            best_val = None
            for c in pool:
                r = c[5]
                v = _evaluate(r[0], r[1], r[2], r[3], r[4], opp_off)
                if best_val is None or v > best_val:
                    best_val = v
                    best = c
        except Exception:
            pass

        order, f1, f2 = best[0], best[1], best[2]
        if f1 == 'P' and f2 == 'P':
            return "H:P,P"
        if f1 == 'P':
            # Normalize: actual move in the first slot.
            order = 'L' if order == 'H' else 'H'
            f1, f2 = f2, 'P'
        return order + ':' + f1 + ',' + f2
    except Exception:
        return "H:P,P"
