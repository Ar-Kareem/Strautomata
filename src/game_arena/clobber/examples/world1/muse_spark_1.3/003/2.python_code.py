
import time
import random
import sys
sys.setrecursionlimit(10000)

NROWS = 5
NCOLS = 6
N = 30
WIN = 10000

NEIGH = []
for r in range(NROWS):
    for c in range(NCOLS):
        i = r*NCOLS+c
        lst = []
        if r > 0: lst.append((r-1)*NCOLS+c)
        if r+1 < NROWS: lst.append((r+1)*NCOLS+c)
        if c > 0: lst.append(r*NCOLS+c-1)
        if c+1 < NCOLS: lst.append(r*NCOLS+c+1)
        NEIGH.append(lst)

W = []
for r in range(NROWS):
    for c in range(NCOLS):
        W.append(min(r, NROWS-1-r) + min(c, NCOLS-1-c))

try:
    import numpy as _np
    _HAS_NP = True
except Exception:
    _HAS_NP = False

class _Timeout(Exception):
    pass

def _to_bits(a):
    if _HAS_NP:
        try:
            arr = _np.asarray(a).reshape(-1)
            bits = 0
            for i, v in enumerate(arr):
                if int(v) == 1:
                    bits |= (1 << i)
            return bits
        except Exception:
            pass
    # pure python fallback
    bits = 0
    # try 2D list
    try:
        if isinstance(a, (list, tuple)) and len(a) == NROWS and isinstance(a[0], (list, tuple)):
            for r in range(NROWS):
                for c in range(NCOLS):
                    if int(a[r][c]) == 1:
                        bits |= (1 << (r*NCOLS+c))
            return bits
    except Exception:
        pass
    try:
        flat = list(a)
        # if nested, flatten
        tmp = []
        for x in flat:
            if isinstance(x, (list, tuple)):
                tmp.extend(list(x))
            else:
                tmp.append(x)
        flat = tmp
        for i, v in enumerate(flat[:N]):
            if int(v) == 1:
                bits |= (1 << i)
        return bits
    except Exception:
        return 0

def _gen_moves(cur, opp):
    moves = []
    c = cur
    while c:
        lsb = c & -c
        s = lsb.bit_length() - 1
        for nb in NEIGH[s]:
            if (opp >> nb) & 1:
                moves.append((s, nb))
        c ^= lsb
    return moves

def _count_moves(cur, opp):
    cnt = 0
    c = cur
    while c:
        lsb = c & -c
        s = lsb.bit_length() - 1
        for nb in NEIGH[s]:
            if (opp >> nb) & 1:
                cnt += 1
        c ^= lsb
    return cnt

def _central_sum(bits):
    s = 0
    c = bits
    while c:
        lsb = c & -c
        idx = lsb.bit_length() - 1
        s += W[idx]
        c ^= lsb
    return s

def _static_eval(cur, opp):
    m = _count_moves(cur, opp)
    if m == 0:
        return -WIN
    cs = _central_sum(cur) - _central_sum(opp)
    return m * 10 + cs

def _move_to_str(s, d):
    sr = s // NCOLS
    sc = s % NCOLS
    dr = d // NCOLS
    dc = d % NCOLS
    if dr == sr - 1:
        direc = 'U'
    elif dr == sr + 1:
        direc = 'D'
    elif dc == sc - 1:
        direc = 'L'
    else:
        direc = 'R'
    return f"{sr},{sc},{direc}"

def policy(you, opponent) -> str:
    t0 = time.perf_counter()
    deadline = t0 + 0.90
    try:
        cur = _to_bits(you)
        opp = _to_bits(opponent)
        root_moves = _gen_moves(cur, opp)
        if not root_moves:
            return "0,0,U"
        if len(root_moves) == 1:
            s, d = root_moves[0]
            return _move_to_str(s, d)

        # child positions
        childs = []
        for (s, d) in root_moves:
            nc = opp ^ (1 << d)
            no = cur ^ (1 << s) ^ (1 << d)
            childs.append((s, d, nc, no))

        # order by opponent mobility ascending + centrality (cheap)
        scored = []
        for (s, d, nc, no) in childs:
            cm = _count_moves(nc, no)
            # prefer smaller opp mobility, central move
            key = cm * 100 - (W[s] + W[d])
            scored.append((key, s, d, nc, no))
        scored.sort(key=lambda x: x[0])
        ordered = [(s, d, nc, no) for (_, s, d, nc, no) in scored]

        # ---------- iterative deepening negamax ----------
        TT = {}
        nodes = [0]
        best_move = (ordered[0][0], ordered[0][1])
        best_idx = 0
        # scores for ordering next iteration
        root_scores = [0]*len(ordered)

        # local refs for speed
        def negamax(c, o, depth, alpha, beta):
            nodes[0] += 1
            if (nodes[0] & 511) == 0 and time.perf_counter() > deadline - 0.55:
                # leave time for monte carlo; use tighter budget here
                # we raise only if we exceeded negamax budget
                pass
            if (nodes[0] & 1023) == 0 and time.perf_counter() > deadline - 0.05:
                raise _Timeout()
            key = (c, o, depth)
            # TT lookup
            ent = TT.get(key)
            if ent is not None:
                sc_, fl_, _bm = ent
                if fl_ == 0:
                    return sc_
                elif fl_ == 1:
                    if sc_ > alpha:
                        alpha = sc_
                else:
                    if sc_ < beta:
                        beta = sc_
                if alpha >= beta:
                    return sc_
            moves = _gen_moves(c, o)
            if not moves:
                return -WIN - depth
            if depth <= 0:
                return _static_eval(c, o)
            # cheap ordering: central first
            # sort by W sum descending (small list, sort ok)
            moves.sort(key=lambda md: (W[md[0]] + W[md[1]]), reverse=True)
            # use TT best first if available
            if ent is not None and ent[2] is not None:
                bm = ent[2]
                # move bm to front
                try:
                    idx = moves.index(bm)
                    if idx != 0:
                        moves[0], moves[idx] = moves[idx], moves[0]
                except ValueError:
                    pass
            orig_alpha = alpha
            best_local = moves[0]
            best_sc = -10**9
            for (s_, d_) in moves:
                nc_ = o ^ (1 << d_)
                no_ = c ^ (1 << s_) ^ (1 << d_)
                sc = -negamax(nc_, no_, depth-1, -beta, -alpha)
                if sc > best_sc:
                    best_sc = sc
                    best_local = (s_, d_)
                if sc > alpha:
                    alpha = sc
                if alpha >= beta:
                    break
            # store
            if best_sc <= orig_alpha:
                fl = 2
            elif best_sc >= beta:
                fl = 1
            else:
                fl = 0
            TT[key] = (best_sc, fl, best_local)
            return best_sc

        # decide max depth by branching
        total_pieces = bin(cur).count("1") + bin(opp).count("1") if hasattr(int, "bit_count") else bin(cur).count("1") + bin(opp).count("1")
        # use bit_count if available
        try:
            total_pieces = cur.bit_count() + opp.bit_count()
        except Exception:
            pass

        negamax_budget = t0 + 0.30
        # iterative deepening
        max_depth = total_pieces  # full solve in endgame
        # for large branching limit depth to avoid explosion
        if len(ordered) > 20:
            max_depth = min(max_depth, 4)
        elif len(ordered) > 12:
            max_depth = min(max_depth, 6)

        # order indices by current root_scores
        order_idx = list(range(len(ordered)))
        try:
            for depth in range(1, max_depth+1):
                if time.perf_counter() > negamax_budget:
                    break
                # sort by previous scores descending
                if depth > 1:
                    order_idx.sort(key=lambda i: root_scores[i], reverse=True)
                alpha = -10**9
                beta = 10**9
                cur_best_sc = -10**9
                cur_best_i = order_idx[0]
                for ii in order_idx:
                    if time.perf_counter() > negamax_budget:
                        raise _Timeout()
                    s, d, nc, no = ordered[ii]
                    # search child
                    sc = -negamax(nc, no, depth-1, -beta, -alpha)
                    root_scores[ii] = sc
                    if sc > cur_best_sc:
                        cur_best_sc = sc
                        cur_best_i = ii
                    if sc > alpha:
                        alpha = sc
                best_idx = cur_best_i
                best_move = (ordered[best_idx][0], ordered[best_idx][1])
                # if proven win with full depth, can stop early
                if cur_best_sc > WIN - 500 and depth >= 3:
                    # check if fully solved? if depth == total_pieces then proven
                    if depth >= total_pieces - 1:
                        break
                # if proven win and little branching, keep deepening to confirm
                if time.perf_counter() > negamax_budget:
                    break
        except _Timeout:
            pass
        except Exception:
            pass

        # reorder ordered by root_scores for monte carlo prior
        try:
            idx_sorted = sorted(range(len(ordered)), key=lambda i: root_scores[i], reverse=True)
        except Exception:
            idx_sorted = list(range(len(ordered)))
        # map to new order
        ordered2 = [ordered[i] for i in idx_sorted]
        # keep root_scores aligned
        # ---------- Monte Carlo UCB ----------
        nM = len(ordered2)
        wins = [0.0]*nM
        visits = [0]*nM
        total_vis = 0
        # pre extract childs
        cncs = [(o[2], o[3]) for o in ordered2]
        C = 0.7
        it = 0
        # fast locals
        randrange = random.randrange
        try:
            while True:
                if (it & 15) == 0 and time.perf_counter() > deadline - 0.05:
                    break
                # select
                sel = -1
                # first unvisited in order
                for i in range(nM):
                    if visits[i] == 0:
                        sel = i
                        break
                if sel == -1:
                    # UCB
                    import math
                    logt = math.log(total_vis + 1)
                    best_u = -1e9
                    for i in range(nM):
                        wi = wins[i]/visits[i]
                        u = wi + C * ((logt/visits[i]) ** 0.5)
                        if u > best_u:
                            best_u = u
                            sel = i
                # playout from child (opponent to move)
                c0, o0 = cncs[sel]
                c = c0
                o = o0
                ply = 0
                # random playout: True if player to move (c) wins
                while True:
                    # gen
                    mv = []
                    cc = c
                    while cc:
                        lsb = cc & -cc
                        s_ = lsb.bit_length() - 1
                        for nb in NEIGH[s_]:
                            if (o >> nb) & 1:
                                mv.append((s_, nb))
                        cc ^= lsb
                    if not mv:
                        stm_win = (ply & 1) == 1
                        break
                    k = randrange(len(mv))
                    s_, d_ = mv[k]
                    nc_ = o ^ (1 << d_)
                    no_ = c ^ (1 << s_) ^ (1 << d_)
                    c, o = nc_, no_
                    ply += 1
                    if ply > 32:
                        # should not happen, treat as draw -> loss for stm?
                        # use static
                        stm_win = _static_eval(c, o) > 0
                        # adjust for parity? approximate
                        if (ply & 1) == 1:
                            stm_win = not stm_win
                        # Actually we want stm win from original child perspective?
                        # Simplify: evaluate from current player perspective
                        break
                root_win = (not stm_win)  # root wins if child stm loses
                visits[sel] += 1
                total_vis += 1
                if root_win:
                    wins[sel] += 1.0
                it += 1
                if it > 20000:
                    break
        except _Timeout:
            pass
        except Exception:
            pass

        # choose final move
        try:
            if total_vis > 0:
                # best win rate, require at least 1 visit
                best_rate = -1
                best_sel = best_idx  # fallback mapping?
                # map best_idx (in old ordering) to new ordering? Simplify: evaluate all
                for i in range(nM):
                    if visits[i] == 0:
                        continue
                    rate = wins[i]/visits[i]
                    # tie-break by root_scores
                    # find original score
                    tie = (idx_sorted[i] < len(root_scores) and root_scores[idx_sorted[i]] or 0) * 1e-4
                    if rate + tie*0.001 > best_rate:
                        best_rate = rate + tie*0.001
                        best_sel = i
                s, d, _, _ = ordered2[best_sel]
                return _move_to_str(s, d)
            else:
                s, d = best_move
                return _move_to_str(s, d)
        except Exception:
            s, d = best_move
            return _move_to_str(s, d)
    except Exception:
        pass
    # emergency fallback: scan for any legal move
    try:
        cur = _to_bits(you)
        opp = _to_bits(opponent)
        c = cur
        while c:
            lsb = c & -c
            s = lsb.bit_length() - 1
            sr = s // NCOLS
            sc = s % NCOLS
            # try dirs
            if sr > 0 and ((opp >> (s-NCOLS)) & 1):
                return f"{sr},{sc},U"
            if sr+1 < NROWS and ((opp >> (s+NCOLS)) & 1):
                return f"{sr},{sc},D"
            if sc > 0 and ((opp >> (s-1)) & 1):
                return f"{sr},{sc},L"
            if sc+1 < NCOLS and ((opp >> (s+1)) & 1):
                return f"{sr},{sc},R"
            c ^= lsb
    except Exception:
        pass
    return "0,0,U"
