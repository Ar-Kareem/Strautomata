
import time

MAN_VAL = 100
KING_VAL = 140
INF = 100000
_DEADLINE = 0.0
_NODES = 0

class _Timeout(Exception):
    pass

def _gen_moves(my_men, my_kings, opp_men, opp_kings, color):
    occ = my_men | my_kings | opp_men | opp_kings
    opp = opp_men | opp_kings
    fwd = 1 if color == 'w' else -1
    cap_fwd = []
    cap_bwd = []
    for p in my_men:
        r = p // 8
        c = p - r * 8
        # forward captures
        tr = r + 2 * fwd
        if 0 <= tr < 8:
            mr = r + fwd
            # dc = -1
            tc = c - 2
            if 0 <= tc < 8:
                mid = mr * 8 + (c - 1)
                dst = tr * 8 + tc
                if mid in opp and dst not in occ:
                    cap_fwd.append((p, dst, mid, False))
            # dc = +1
            tc = c + 2
            if 0 <= tc < 8:
                mid = mr * 8 + (c + 1)
                dst = tr * 8 + tc
                if mid in opp and dst not in occ:
                    cap_fwd.append((p, dst, mid, False))
        # backward captures
        trb = r - 2 * fwd
        if 0 <= trb < 8:
            mrb = r - fwd
            tcb = c - 2
            if 0 <= tcb < 8:
                mid = mrb * 8 + (c - 1)
                dst = trb * 8 + tcb
                if mid in opp and dst not in occ:
                    cap_bwd.append((p, dst, mid, False))
            tcb = c + 2
            if 0 <= tcb < 8:
                mid = mrb * 8 + (c + 1)
                dst = trb * 8 + tcb
                if mid in opp and dst not in occ:
                    cap_bwd.append((p, dst, mid, False))
    for p in my_kings:
        r = p // 8
        c = p - r * 8
        # 4 dirs
        # (1,1)
        mr = r + 1; mc = c + 1; tr = r + 2; tc = c + 2
        if 0 <= tr < 8 and 0 <= tc < 8:
            mid = mr * 8 + mc; dst = tr * 8 + tc
            if mid in opp and dst not in occ:
                cap_fwd.append((p, dst, mid, True))
        mr = r + 1; mc = c - 1; tr = r + 2; tc = c - 2
        if 0 <= tr < 8 and 0 <= tc < 8:
            mid = mr * 8 + mc; dst = tr * 8 + tc
            if mid in opp and dst not in occ:
                cap_fwd.append((p, dst, mid, True))
        mr = r - 1; mc = c + 1; tr = r - 2; tc = c + 2
        if 0 <= tr < 8 and 0 <= tc < 8:
            mid = mr * 8 + mc; dst = tr * 8 + tc
            if mid in opp and dst not in occ:
                cap_fwd.append((p, dst, mid, True))
        mr = r - 1; mc = c - 1; tr = r - 2; tc = c - 2
        if 0 <= tr < 8 and 0 <= tc < 8:
            mid = mr * 8 + mc; dst = tr * 8 + tc
            if mid in opp and dst not in occ:
                cap_fwd.append((p, dst, mid, True))
    if cap_fwd:
        return cap_fwd
    if cap_bwd:
        return cap_bwd
    quiets = []
    for p in my_men:
        r = p // 8
        c = p - r * 8
        tr = r + fwd
        if 0 <= tr < 8:
            tc = c - 1
            if 0 <= tc < 8:
                dst = tr * 8 + tc
                if dst not in occ:
                    quiets.append((p, dst, None, False))
            tc = c + 1
            if 0 <= tc < 8:
                dst = tr * 8 + tc
                if dst not in occ:
                    quiets.append((p, dst, None, False))
    for p in my_kings:
        r = p // 8
        c = p - r * 8
        tr = r + 1; tc = c + 1
        if 0 <= tr < 8 and 0 <= tc < 8:
            dst = tr * 8 + tc
            if dst not in occ:
                quiets.append((p, dst, None, True))
        tr = r + 1; tc = c - 1
        if 0 <= tr < 8 and 0 <= tc < 8:
            dst = tr * 8 + tc
            if dst not in occ:
                quiets.append((p, dst, None, True))
        tr = r - 1; tc = c + 1
        if 0 <= tr < 8 and 0 <= tc < 8:
            dst = tr * 8 + tc
            if dst not in occ:
                quiets.append((p, dst, None, True))
        tr = r - 1; tc = c - 1
        if 0 <= tr < 8 and 0 <= tc < 8:
            dst = tr * 8 + tc
            if dst not in occ:
                quiets.append((p, dst, None, True))
    return quiets

def _eval(my_men, my_kings, opp_men, opp_kings, color):
    s = (len(my_men) - len(opp_men)) * MAN_VAL + (len(my_kings) - len(opp_kings)) * KING_VAL
    if color == 'w':
        for p in my_men:
            r = p // 8; c = p - r * 8
            s += r * 5
            if 2 <= c <= 5:
                s += 2
            else:
                if c == 0 or c == 7:
                    s -= 4
            if r == 0 or r == 1:
                s += 3
        for p in opp_men:
            r = p // 8; c = p - r * 8
            s -= (7 - r) * 5
            if 2 <= c <= 5:
                s -= 2
            else:
                if c == 0 or c == 7:
                    s += 4
            if r == 7 or r == 6:
                s -= 3
    else:
        for p in my_men:
            r = p // 8; c = p - r * 8
            s += (7 - r) * 5
            if 2 <= c <= 5:
                s += 2
            else:
                if c == 0 or c == 7:
                    s -= 4
            if r == 7 or r == 6:
                s += 3
        for p in opp_men:
            r = p // 8; c = p - r * 8
            s -= r * 5
            if 2 <= c <= 5:
                s -= 2
            else:
                if c == 0 or c == 7:
                    s += 4
            if r == 0 or r == 1:
                s -= 3
    for p in my_kings:
        r = p // 8; c = p - r * 8
        d = abs(r - 3.5) + abs(c - 3.5)
        s += int(6 - d)
        if c == 0 or c == 7:
            s -= 3
    for p in opp_kings:
        r = p // 8; c = p - r * 8
        d = abs(r - 3.5) + abs(c - 3.5)
        s -= int(6 - d)
        if c == 0 or c == 7:
            s += 3
    s += 5
    return s

def _apply_move(my_men, my_kings, opp_men, opp_kings, fr, to, cap, is_king, prom_row):
    if is_king:
        n_my_kings = my_kings.copy()
        n_my_kings.remove(fr)
        n_my_kings.add(to)
        n_my_men = my_men
    else:
        if (to // 8) == prom_row:
            n_my_men = my_men.copy()
            n_my_men.remove(fr)
            n_my_kings = my_kings.copy()
            n_my_kings.add(to)
        else:
            n_my_men = my_men.copy()
            n_my_men.remove(fr)
            n_my_men.add(to)
            n_my_kings = my_kings
    if cap is not None:
        if cap in opp_kings:
            n_opp_kings = opp_kings.copy()
            n_opp_kings.remove(cap)
            n_opp_men = opp_men
        elif cap in opp_men:
            n_opp_men = opp_men.copy()
            n_opp_men.remove(cap)
            n_opp_kings = opp_kings
        else:
            n_opp_men = opp_men
            n_opp_kings = opp_kings
    else:
        n_opp_men = opp_men
        n_opp_kings = opp_kings
    return n_my_men, n_my_kings, n_opp_men, n_opp_kings

def _move_order_score(fr, to, cap, is_king, opp_kings, prom_row):
    sc = 0
    if cap is not None:
        sc += 2000
        if cap in opp_kings:
            sc += 200
        else:
            sc += 100
    if not is_king and (to // 8) == prom_row:
        sc += 800
    c = to % 8; r = to // 8
    if 2 <= c <= 5:
        sc += 10
    if 2 <= r <= 5:
        sc += 10
    if c == 0 or c == 7:
        sc -= 12
    return sc

def _negamax(my_men, my_kings, opp_men, opp_kings, color, depth, alpha, beta, ply):
    global _NODES, _DEADLINE
    _NODES += 1
    if (_NODES & 1023) == 0 and time.time() > _DEADLINE:
        raise _Timeout()
    moves = _gen_moves(my_men, my_kings, opp_men, opp_kings, color)
    if not moves:
        return -10000 + ply
    is_cap = moves[0][2] is not None
    if depth <= 0:
        if not is_cap:
            return _eval(my_men, my_kings, opp_men, opp_kings, color)
        if depth <= -4:
            return _eval(my_men, my_kings, opp_men, opp_kings, color)
    prom_row = 7 if color == 'w' else 0
    # order
    scored = []
    for m in moves:
        fr, to, cap, isk = m
        sc = _move_order_score(fr, to, cap, isk, opp_kings, prom_row)
        scored.append((sc, m))
    scored.sort(key=lambda x: x[0], reverse=True)
    best = -INF
    opp_color = 'b' if color == 'w' else 'w'
    for _, (fr, to, cap, isk) in scored:
        n_my_men, n_my_kings, n_opp_men, n_opp_kings = _apply_move(my_men, my_kings, opp_men, opp_kings, fr, to, cap, isk, prom_row)
        val = -_negamax(n_opp_men, n_opp_kings, n_my_men, n_my_kings, opp_color, depth - 1, -beta, -alpha, ply + 1)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    global _DEADLINE, _NODES
    t0 = time.time()
    _DEADLINE = t0 + 0.90
    _NODES = 0
    try:
        my_men_s = set(r * 8 + c for (r, c) in my_men)
        my_kings_s = set(r * 8 + c for (r, c) in my_kings)
        opp_men_s = set(r * 8 + c for (r, c) in opp_men)
        opp_kings_s = set(r * 8 + c for (r, c) in opp_kings)
        moves = _gen_moves(my_men_s, my_kings_s, opp_men_s, opp_kings_s, color)
        if not moves:
            # no moves: return something from own piece if possible
            allmine = list(my_men) + list(my_kings)
            if allmine:
                fr = allmine[0]
                return (tuple(fr), tuple(fr))
            return ((0, 0), (1, 1))
        if len(moves) == 1:
            fr, to, _, _ = moves[0]
            return ((fr // 8, fr % 8), (to // 8, to % 8))
        prom_row = 7 if color == 'w' else 0
        # initial order
        scored0 = []
        for m in moves:
            fr, to, cap, isk = m
            sc = _move_order_score(fr, to, cap, isk, opp_kings_s, prom_row)
            scored0.append((sc, m))
        scored0.sort(key=lambda x: x[0], reverse=True)
        ordered = [m for _, m in scored0]
        best_move = ordered[0]
        opp_color = 'b' if color == 'w' else 'w'
        # iterative deepening
        for depth in range(1, 20):
            if time.time() > _DEADLINE - 0.06:
                break
            alpha = -INF
            beta = INF
            cur_best = best_move
            cur_best_score = -INF
            # search each root move
            # re-score ordered from previous iteration is already good; keep it
            for (fr, to, cap, isk) in list(ordered):
                n_my_men, n_my_kings, n_opp_men, n_opp_kings = _apply_move(my_men_s, my_kings_s, opp_men_s, opp_kings_s, fr, to, cap, isk, prom_row)
                try:
                    score = -_negamax(n_opp_men, n_opp_kings, n_my_men, n_my_kings, opp_color, depth - 1, -beta, -alpha, 1)
                except _Timeout:
                    raise _Timeout()
                if score > cur_best_score:
                    cur_best_score = score
                    cur_best = (fr, to, cap, isk)
                if score > alpha:
                    alpha = score
            best_move = cur_best
            # reorder for next depth by last scores: simple bubble using cur scores
            # recompute ordering: put best first
            # to get full ordering, score all root moves with shallow eval? just move best to front
            ordered.remove(best_move)
            ordered.insert(0, best_move)
            if cur_best_score > 9000:
                break
            # if time low break
            if time.time() > _DEADLINE - 0.08:
                break
        fr, to, _, _ = best_move
        return ((fr // 8, fr % 8), (to // 8, to % 8))
    except _Timeout:
        try:
            # return best found so far
            if 'best_move' in locals() and best_move is not None:
                fr, to = best_move[0], best_move[1]
                return ((fr // 8, fr % 8), (to // 8, to % 8))
            if 'moves' in locals() and moves:
                fr, to = moves[0][0], moves[0][1]
                return ((fr // 8, fr % 8), (to // 8, to % 8))
        except Exception:
            pass
    except Exception:
        pass
    # ultimate fallback: brute force legal-ish move
    try:
        occ = set(my_men) | set(my_kings) | set(opp_men) | set(opp_kings)
        opps = set(opp_men) | set(opp_kings)
        fwd = 1 if color == 'w' else -1
        # forward captures
        for (r, c) in list(my_men) + list(my_kings):
            is_k = (r, c) in set(my_kings)
            dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1)] if is_k else [(fwd, 1), (fwd, -1)]
            for dr, dc in dirs:
                mr, mc = r + dr, c + dc
                tr, tc = r + 2 * dr, c + 2 * dc
                if 0 <= tr < 8 and 0 <= tc < 8:
                    if (mr, mc) in opps and (tr, tc) not in occ:
                        return ((r, c), (tr, tc))
        # backward captures for men
        for (r, c) in list(my_men):
            for dr, dc in [(-fwd, 1), (-fwd, -1)]:
                mr, mc = r + dr, c + dc
                tr, tc = r + 2 * dr, c + 2 * dc
                if 0 <= tr < 8 and 0 <= tc < 8:
                    if (mr, mc) in opps and (tr, tc) not in occ:
                        return ((r, c), (tr, tc))
        # quiets
        for (r, c) in list(my_men) + list(my_kings):
            is_k = (r, c) in set(my_kings)
            dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1)] if is_k else [(fwd, 1), (fwd, -1)]
            for dr, dc in dirs:
                tr, tc = r + dr, c + dc
                if 0 <= tr < 8 and 0 <= tc < 8:
                    if (tr, tc) not in occ:
                        return ((r, c), (tr, tc))
        # emergency any
        allmine = list(my_men) + list(my_kings)
        if allmine:
            fr = allmine[0]
            r, c = fr
            for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                tr, tc = r + dr, c + dc
                if 0 <= tr < 8 and 0 <= tc < 8:
                    if (tr, tc) not in occ:
                        return ((r, c), (tr, tc))
            return ((r, c), (r, c))
    except Exception:
        pass
    return ((2, 1), (3, 0))
