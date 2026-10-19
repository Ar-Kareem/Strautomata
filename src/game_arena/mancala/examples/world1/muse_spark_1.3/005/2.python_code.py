
import time

_INF = 1000000

class _Timeout(Exception):
    pass

def _apply_move(mp, ms, op, os, mv):
    nmp = mp[:]
    nop = op[:]
    s = nmp[mv]
    nmp[mv] = 0
    nms = ms
    nos = os
    pos = mv + 1
    seeds = s
    last_side = -1
    last_idx = -1
    while True:
        while pos < 6 and seeds > 0:
            nmp[pos] += 1
            seeds -= 1
            if seeds == 0:
                last_side = 0
                last_idx = pos
                break
            pos += 1
        if seeds == 0:
            break
        if pos == 6:
            nms += 1
            seeds -= 1
            if seeds == 0:
                last_side = 2
                break
            for k in range(6):
                if seeds == 0:
                    break
                nop[k] += 1
                seeds -= 1
                if seeds == 0:
                    last_side = 1
                    last_idx = k
                    break
            if seeds == 0:
                break
            pos = 0
        else:
            pos = 0
    extra = (last_side == 2)
    is_cap = False
    cap_gain = 0
    if last_side == 0 and nmp[last_idx] == 1:
        oi = 5 - last_idx
        if nop[oi] > 0:
            cap_gain = nop[oi] + 1
            nms += cap_gain
            nmp[last_idx] = 0
            nop[oi] = 0
            is_cap = True
    s_my = nmp[0]+nmp[1]+nmp[2]+nmp[3]+nmp[4]+nmp[5]
    s_op = nop[0]+nop[1]+nop[2]+nop[3]+nop[4]+nop[5]
    term = None
    if s_my == 0 or s_op == 0:
        term = (nms + s_my) - (nos + s_op)
    return (nmp, nms, nop, nos, extra, is_cap, cap_gain, term)


def policy(you: list[int], opponent: list[int]) -> int:
    import time as _t
    start = _t.perf_counter()
    deadline = start + 0.88
    try:
        mp0 = [int(you[i]) for i in range(6)]
        ms0 = int(you[6])
        op0 = [int(opponent[i]) for i in range(6)]
        os0 = int(opponent[6])
    except Exception:
        for i in range(6):
            try:
                if you[i] > 0:
                    return i
            except Exception:
                pass
        return 0
    legal0 = [i for i in range(6) if mp0[i] > 0]
    if not legal0:
        return 0
    if len(legal0) == 1:
        return legal0[0]

    nodes = [0]

    def do_eval(mp, ms, op, os):
        sd = ms - os
        my_sum = mp[0]+mp[1]+mp[2]+mp[3]+mp[4]+mp[5]
        op_sum = op[0]+op[1]+op[2]+op[3]+op[4]+op[5]
        total = my_sum + op_sum
        # adaptive pit weight: low early, ~1 late
        try:
            w = 0.30 + 0.70 * (1.0 - total / 48.0)
        except Exception:
            w = 0.4
        if w < 0.25:
            w = 0.25
        if w > 1.0:
            w = 1.0
        my_free = 0
        op_free = 0
        for i in range(6):
            a = mp[i]
            if a != 0 and (a - (6 - i)) % 13 == 0:
                my_free += 1
            b = op[i]
            if b != 0 and (b - (6 - i)) % 13 == 0:
                op_free += 1
        my_cap = 0
        op_cap = 0
        mob_my = 0
        mob_op = 0
        for i in range(6):
            if mp[i] == 0:
                my_cap += op[5 - i]
            else:
                mob_my += 1
            if op[i] == 0:
                op_cap += mp[5 - i]
            else:
                mob_op += 1
        score = sd + w * (my_sum - op_sum) + 0.6 * (my_free - op_free) + 0.08 * (my_cap - op_cap) + 0.05 * (mob_my - mob_op)
        return score

    def qsearch(mp, ms, op, os, alpha, beta, qd):
        nodes[0] += 1
        if (nodes[0] & 255) == 0 and _t.perf_counter() > deadline:
            raise _Timeout()
        s_my = mp[0]+mp[1]+mp[2]+mp[3]+mp[4]+mp[5]
        s_op = op[0]+op[1]+op[2]+op[3]+op[4]+op[5]
        if s_my == 0:
            return ms - os - s_op
        if s_op == 0:
            return ms + s_my - os
        stand = do_eval(mp, ms, op, os)
        if qd <= 0:
            return stand
        if stand >= beta:
            return stand
        # collect tactical moves
        tacs = []
        for mv in range(6):
            if mp[mv] == 0:
                continue
            nmp, nms, nop, nos, extra, is_cap, cap_gain, term = _apply_move(mp, ms, op, os, mv)
            if extra or is_cap or term is not None:
                tacs.append((mv, nmp, nms, nop, nos, extra, is_cap, cap_gain, term))
        if not tacs:
            return stand
        # order: extra first, then capture gain
        tacs.sort(key=lambda x: (x[5], x[6], x[7]), reverse=True)
        best = stand
        if best > alpha:
            alpha = best
        for _, nmp, nms, nop, nos, extra, is_cap, cap_gain, term in tacs:
            if term is not None:
                sc = term
            elif extra:
                sc = qsearch(nmp, nms, nop, nos, alpha, beta, qd - 1)
            else:
                sc = -qsearch(nop, nos, nmp, nms, -beta, -alpha, qd - 1)
            if sc > best:
                best = sc
                if best > alpha:
                    alpha = best
                    if alpha >= beta:
                        break
        return best

    def negamax(mp, ms, op, os, depth, alpha, beta):
        nodes[0] += 1
        if (nodes[0] & 255) == 0 and _t.perf_counter() > deadline:
            raise _Timeout()
        s_my = mp[0]+mp[1]+mp[2]+mp[3]+mp[4]+mp[5]
        s_op = op[0]+op[1]+op[2]+op[3]+op[4]+op[5]
        if s_my == 0:
            return ms - os - s_op
        if s_op == 0:
            return ms + s_my - os
        if depth <= 0:
            return qsearch(mp, ms, op, os, alpha, beta, 2)
        childs = []
        for mv in range(6):
            if mp[mv] == 0:
                continue
            nmp, nms, nop, nos, extra, is_cap, cap_gain, term = _apply_move(mp, ms, op, os, mv)
            # ordering key
            key = cap_gain + (50 if is_cap else 0) + (100 if extra else 0)
            if term is not None:
                # winning terminal very good
                if term > 0:
                    key += 10000 + term
                else:
                    key += term
            childs.append((key, mv, nmp, nms, nop, nos, extra, term))
        childs.sort(key=lambda x: x[0], reverse=True)
        best = -_INF
        for _, mv, nmp, nms, nop, nos, extra, term in childs:
            if term is not None:
                sc = term
            elif extra:
                sc = negamax(nmp, nms, nop, nos, depth - 1, alpha, beta)
            else:
                sc = -negamax(nop, nos, nmp, nms, depth - 1, -beta, -alpha)
            if sc > best:
                best = sc
                if best > alpha:
                    alpha = best
                    if alpha >= beta:
                        break
        return best

    # root children precompute for fallback ordering
    try:
        root_info = []
        for mv in legal0:
            nmp, nms, nop, nos, extra, is_cap, cap_gain, term = _apply_move(mp0, ms0, op0, os0, mv)
            root_info.append([mv, nmp, nms, nop, nos, extra, is_cap, cap_gain, term])
        # heuristic fallback best
        def hkey(r):
            _, _, nms, _, _, extra, is_cap, cap_gain, term = r
            if term is not None:
                return 20000 + term
            return (1000 if extra else 0) + (500 if is_cap else 0) + cap_gain * 10 + (nms - ms0) * 5 + r[0] * 0.1
        root_info.sort(key=hkey, reverse=True)
        best_move = root_info[0][0]
        prev_scores = {}
        for r in root_info:
            prev_scores[r[0]] = hkey(r)
        max_depth = 12
        for depth in range(1, max_depth + 1):
            if _t.perf_counter() > deadline - 0.05:
                break
            # order by previous scores
            root_info.sort(key=lambda r: prev_scores.get(r[0], 0), reverse=True)
            alpha = -_INF
            beta = _INF
            cur_scores = {}
            cur_best = best_move
            cur_best_score = -_INF
            for r in root_info:
                mv, nmp, nms, nop, nos, extra, is_cap, cap_gain, term = r
                if _t.perf_counter() > deadline - 0.02:
                    raise _Timeout()
                if term is not None:
                    sc = term
                elif extra:
                    sc = negamax(nmp, nms, nop, nos, depth - 1, alpha, beta)
                else:
                    sc = -negamax(nop, nos, nmp, nms, depth - 1, -beta, -alpha)
                cur_scores[mv] = sc
                if sc > cur_best_score:
                    cur_best_score = sc
                    cur_best = mv
                if sc > alpha:
                    alpha = sc
            prev_scores = cur_scores
            best_move = cur_best
            # early exit on forced win/loss large
            if abs(cur_best_score) > 900000:
                break
            # if winning by a lot and time short, stop
            if depth >= 6 and _t.perf_counter() > deadline - 0.15:
                break
        return best_move
    except _Timeout:
        # return best found so far
        try:
            return best_move
        except Exception:
            pass
    except Exception:
        pass
    # ultimate fallback: heuristic
    try:
        fb_best = legal0[0]
        fb_score = -10**9
        for mv in legal0:
            _, nms, _, _, extra, is_cap, cap_gain, term = _apply_move(mp0, ms0, op0, os0, mv)
            s = 0
            if term is not None:
                s = 10000 + term
            else:
                if extra:
                    s += 1000
                if is_cap:
                    s += 500 + cap_gain * 10
                s += (nms - ms0) * 5
                s += mv * 0.1
            if s > fb_score:
                fb_score = s
                fb_best = mv
        return fb_best
    except Exception:
        return legal0[0]
