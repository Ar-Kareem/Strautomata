
import numpy as np
import time
import collections

N = 6
NSQ = 36
_DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

RAYS = [[] for _ in range(NSQ)]
KING_NB = [[] for _ in range(NSQ)]
for r in range(N):
    for c in range(N):
        idx = r*N+c
        for dr, dc in _DIRS:
            ray = []
            rr, cc = r+dr, c+dc
            while 0 <= rr < N and 0 <= cc < N:
                ray.append(rr*N+cc)
                rr += dr
                cc += dc
            RAYS[idx].append(ray)
        nb = []
        for dr, dc in _DIRS:
            rr, cc = r+dr, c+dc
            if 0 <= rr < N and 0 <= cc < N:
                nb.append(rr*N+cc)
        KING_NB[idx] = nb

MATE = 10000
INF = 10**9
_has_bit_count = hasattr(int, "bit_count")

class _Timeout(Exception):
    pass

def _queen_moves_list(pos, occ):
    res = []
    for ray in RAYS[pos]:
        for sq in ray:
            if (occ >> sq) & 1:
                break
            res.append(sq)
    return res

def _queen_count(pos, occ):
    c = 0
    for ray in RAYS[pos]:
        for sq in ray:
            if (occ >> sq) & 1:
                break
            c += 1
    return c

def _king_dists(sources, occ):
    dist = [99]*NSQ
    dq = collections.deque()
    for s in sources:
        if dist[s] != 0:
            dist[s] = 0
            dq.append(s)
    while dq:
        cur = dq.popleft()
        nd = dist[cur]+1
        for nb in KING_NB[cur]:
            if dist[nb] != 99:
                continue
            if (occ >> nb) & 1:
                continue
            dist[nb] = nd
            dq.append(nb)
    return dist

def _static_eval(cur, opp, occ):
    mob_cur = 0
    for p in cur:
        mob_cur += _queen_count(p, occ)
    if mob_cur == 0:
        return -MATE
    mob_opp = 0
    for p in opp:
        mob_opp += _queen_count(p, occ)
    if mob_opp == 0:
        return MATE
    d_cur = _king_dists(cur, occ)
    d_opp = _king_dists(opp, occ)
    terr = 0
    for i in range(NSQ):
        if (occ >> i) & 1:
            continue
        dc = d_cur[i]
        do = d_opp[i]
        if dc < do:
            terr += 1
        elif dc > do:
            terr -= 1
    if _has_bit_count:
        empty = NSQ - occ.bit_count()
    else:
        empty = NSQ - bin(occ).count("1")
    if empty > 22:
        wm, wt = 3, 1
    elif empty > 12:
        wm, wt = 2, 2
    else:
        wm, wt = 1, 4
    return (mob_cur - mob_opp)*wm + terr*wt

def _cheap_order_key(to, ar, om, on, opp_reach_set):
    dc = _queen_count(to, on)
    bonus = 12 if ar in opp_reach_set else 0
    return dc + bonus

def policy(board) -> str:
    start = time.time()
    deadline = start + 0.88
    try:
        my_pos = []
        opp_pos = []
        occ = 0
        for r in range(6):
            for c in range(6):
                v = int(board[r, c])
                idx = r*6+c
                if v == 1:
                    my_pos.append(idx)
                    occ |= (1 << idx)
                elif v == 2:
                    opp_pos.append(idx)
                    occ |= (1 << idx)
                elif v == -1:
                    occ |= (1 << idx)
        # generate root moves
        root_raw = []
        for fr in my_pos:
            dests = _queen_moves_list(fr, occ)
            for to in dests:
                om = (occ ^ (1 << fr)) | (1 << to)
                arrows = _queen_moves_list(to, om)
                for ar in arrows:
                    on = om | (1 << ar)
                    root_raw.append((fr, to, ar, om, on))
        if not root_raw:
            return "0,0:0,0:0,0"
        if len(root_raw) == 1:
            fr, to, ar, _, _ = root_raw[0]
            return f"{fr//6},{fr%6}:{to//6},{to%6}:{ar//6},{ar%6}"
        # initial cheap ordering so early timeout still good
        # compute opp reach per om cache
        cache0 = {}
        tmp = []
        for fr, to, ar, om, on in root_raw:
            s = cache0.get(om)
            if s is None:
                s = set()
                for op in opp_pos:
                    for ray in RAYS[op]:
                        for sq in ray:
                            if (om >> sq) & 1:
                                break
                            s.add(sq)
                cache0[om] = s
            h = _queen_count(to, on) + (12 if ar in s else 0)
            tmp.append((h, (fr, to, ar, om, on)))
        tmp.sort(key=lambda x: x[0], reverse=True)
        ordered_raw = [m for _, m in tmp]
        fallback_fr, fallback_to, fallback_ar = ordered_raw[0][0], ordered_raw[0][1], ordered_raw[0][2]
        fallback_str = f"{fallback_fr//6},{fallback_fr%6}:{fallback_to//6},{fallback_to%6}:{fallback_ar//6},{fallback_ar%6}"
        # 1-ply full eval
        scored = []
        best_score = -INF
        best_tuple = (fallback_fr, fallback_to, fallback_ar)
        for fr, to, ar, om, on in ordered_raw:
            if time.time() > deadline - 0.06:
                break
            new_my = [(to if p == fr else p) for p in my_pos]
            s_opp = _static_eval(opp_pos, new_my, on)
            s_root = -s_opp
            # tiny deterministic tie breaker favouring centre arrows
            # centre bonus small
            ar_r, ar_c = ar//6, ar%6
            centre = - (abs(ar_r-2.5)+abs(ar_c-2.5))*0.01
            s_root = s_root + centre
            new_my_t = new_my
            scored.append((s_root, (fr, to, ar, om, on, new_my_t)))
            if s_root > best_score:
                best_score = s_root
                best_tuple = (fr, to, ar)
                if s_root >= 9000:
                    return f"{fr//6},{fr%6}:{to//6},{to%6}:{ar//6},{ar%6}"
        if not scored:
            return fallback_str
        scored.sort(key=lambda x: x[0], reverse=True)
        cur_best_score = best_score
        cur_best_tuple = best_tuple
        # iterative deepening
        nodes = [0]
        # define negamax closure
        def _negamax(cur, opp, o, depth, alpha, beta, ply):
            nodes[0] += 1
            if (nodes[0] & 255) == 0:
                if time.time() > deadline:
                    raise _Timeout()
            if depth == 0:
                return _static_eval(cur, opp, o)
            moves = []
            for fr in cur:
                dests = _queen_moves_list(fr, o)
                for to in dests:
                    om2 = (o ^ (1 << fr)) | (1 << to)
                    arrs = _queen_moves_list(to, om2)
                    for ar in arrs:
                        on2 = om2 | (1 << ar)
                        moves.append((fr, to, ar, om2, on2))
            if not moves:
                return -MATE + ply
            # order + truncate
            lim = None
            if depth == 1:
                lim = 20
            elif depth == 2:
                lim = 20
            else:
                lim = 12
            if len(moves) > 1:
                cch = {}
                osc = []
                for fr, to, ar, om2, on2 in moves:
                    s = cch.get(om2)
                    if s is None:
                        s = set()
                        for op in opp:
                            for ray in RAYS[op]:
                                for sq in ray:
                                    if (om2 >> sq) & 1:
                                        break
                                    s.add(sq)
                        cch[om2] = s
                    h = _queen_count(to, on2) + (12 if ar in s else 0)
                    osc.append((h, (fr, to, ar, om2, on2)))
                osc.sort(key=lambda x: x[0], reverse=True)
                if lim is not None and len(osc) > lim:
                    osc = osc[:lim]
                moves = [m for _, m in osc]
            best = -INF
            for fr, to, ar, om2, on2 in moves:
                new_cur_pieces = [(to if p == fr else p) for p in cur]
                val = -_negamax(opp, new_cur_pieces, on2, depth-1, -beta, -alpha, ply+1)
                if val > best:
                    best = val
                    if best >= beta:
                        break
                    if best > alpha:
                        alpha = best
            return best
        # try depths 2..6
        for D in (2, 3, 4, 5, 6):
            if time.time() > deadline - 0.08:
                break
            # root width limit
            if D >= 4:
                RL = min(len(scored), 10)
            elif D == 3:
                RL = min(len(scored), 15)
            else:
                RL = min(len(scored), 30)
            # if endgame small branching, use full width
            if len(scored) <= 12:
                RL = len(scored)
            alpha = -INF
            beta = INF
            local_best = -INF
            local_tuple = cur_best_tuple
            try:
                for i in range(RL):
                    if time.time() > deadline - 0.02:
                        raise _Timeout()
                    _, (fr, to, ar, om, on, new_my) = scored[i]
                    v_opp = _negamax(opp_pos, new_my, on, D-1, -beta, -alpha, 1)
                    v = -v_opp
                    if v > local_best:
                        local_best = v
                        local_tuple = (fr, to, ar)
                    if v > alpha:
                        alpha = v
                # completed depth without timeout -> adopt
                cur_best_score = local_best
                cur_best_tuple = local_tuple
                if cur_best_score >= 9000:
                    break
                # if winning margin large and deep enough, stop
            except _Timeout:
                break
        fr, to, ar = cur_best_tuple
        return f"{fr//6},{fr%6}:{to//6},{to%6}:{ar//6},{ar%6}"
    except _Timeout:
        try:
            # try to return best found via simple scan
            my2 = []
            occ2 = 0
            for r in range(6):
                for c in range(6):
                    v = int(board[r, c])
                    idx = r*6+c
                    if v == 1:
                        my2.append(idx)
                    if v != 0:
                        if v in (1, 2, -1):
                            occ2 |= (1 << idx)
            for fr in my2:
                dests = _queen_moves_list(fr, occ2)
                for to in dests:
                    om = (occ2 ^ (1 << fr)) | (1 << to)
                    arrs = _queen_moves_list(to, om)
                    if arrs:
                        ar = arrs[0]
                        return f"{fr//6},{fr%6}:{to//6},{to%6}:{ar//6},{ar%6}"
        except Exception:
            pass
        return "0,0:0,0:0,0"
    except Exception:
        try:
            my2 = []
            occ2 = 0
            for r in range(6):
                for c in range(6):
                    v = int(board[r, c])
                    idx = r*6+c
                    if v == 1:
                        my2.append(idx)
                    if v != 0:
                        occ2 |= (1 << idx)
            for fr in my2:
                dests = _queen_moves_list(fr, occ2)
                for to in dests:
                    om = (occ2 ^ (1 << fr)) | (1 << to)
                    arrs = _queen_moves_list(to, om)
                    if arrs:
                        ar = arrs[0]
                        return f"{fr//6},{fr%6}:{to//6},{to%6}:{ar//6},{ar%6}"
        except Exception:
            pass
        return "0,0:0,0:0,0"
