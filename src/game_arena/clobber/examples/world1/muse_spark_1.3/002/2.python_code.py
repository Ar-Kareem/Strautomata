
import time

ROWS = 5
COLS = 6
N = 30
INF = 200000
MATE = 100000

NEIGH = [[] for _ in range(N)]
DIRMAP = {}
for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        for dr, dc, d in [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                j = nr * COLS + nc
                NEIGH[i].append(j)
                DIRMAP[(i, j)] = d

WTABLE = [
    [0, 1, 2, 2, 1, 0],
    [1, 2, 3, 3, 2, 1],
    [2, 3, 4, 4, 3, 2],
    [1, 2, 3, 3, 2, 1],
    [0, 1, 2, 2, 1, 0],
]
W = [0]*N
for r in range(ROWS):
    for c in range(COLS):
        W[r*COLS+c] = WTABLE[r][c]

MOVE_PRIO = {}
for s in range(N):
    for t in NEIGH[s]:
        MOVE_PRIO[(s, t)] = W[s] + W[t]

class Timeout(Exception):
    pass

def board_to_mask(b):
    m = 0
    for r in range(ROWS):
        for c in range(COLS):
            v = 0
            try:
                try:
                    v = b[r][c]
                except Exception:
                    try:
                        v = b[r, c]
                    except Exception:
                        v = b[r*COLS+c]
            except Exception:
                v = 0
            try:
                if int(v) != 0:
                    m |= 1 << (r*COLS+c)
            except Exception:
                pass
    # fallback: if mask empty but input was flat list of 0/1 length 30, try flat
    if m == 0:
        try:
            flat = list(b)
            # check if flat looks like 1D length 30
            if len(flat) == 30:
                for i, vv in enumerate(flat):
                    try:
                        if int(vv) != 0:
                            m |= 1 << i
                    except Exception:
                        pass
        except Exception:
            pass
    return m

def gen_moves_list(cur, opp):
    mv = []
    mm = cur
    while mm:
        lsb = mm & -mm
        s = (lsb.bit_length() - 1)
        for nb in NEIGH[s]:
            if (opp >> nb) & 1:
                mv.append((s, nb))
        mm ^= lsb
    return mv

def policy(you, opponent):
    try:
        cur = board_to_mask(you)
        opp = board_to_mask(opponent)
        # ensure disjoint (in case of bad input)
        # if overlap, prefer you
        # opp = opp & ~cur
        moves = gen_moves_list(cur, opp)
        if not moves:
            return "0,0,U"
        if len(moves) == 1:
            s, t = moves[0]
            return f"{s//COLS},{s%COLS},{DIRMAP[(s,t)]}"

        # initial ordering: central first
        moves.sort(key=lambda x: MOVE_PRIO.get(x, 0), reverse=True)
        best = moves[0]

        start = time.monotonic()
        limit = 0.90
        nodes = [0]
        TT = {}
        EVALC = {}

        def evaluate(c, o):
            key = (c, o)
            v = EVALC.get(key)
            if v is not None:
                return v
            movable_c = 0
            C = 0
            pos = 0
            mm = c
            while mm:
                lsb = mm & -mm
                s = (lsb.bit_length() - 1)
                cnt = 0
                for nb in NEIGH[s]:
                    if (o >> nb) & 1:
                        cnt += 1
                if cnt:
                    movable_c += 1
                    C += cnt
                pos += W[s]
                mm ^= lsb
            movable_o = 0
            mm = o
            while mm:
                lsb = mm & -mm
                s = (lsb.bit_length() - 1)
                for nb in NEIGH[s]:
                    if (c >> nb) & 1:
                        movable_o += 1
                        break
                pos -= W[s]
                mm ^= lsb
            v = 12 * (movable_c - movable_o) + C + pos
            EVALC[key] = v
            return v

        def negamax(c, o, depth, alpha, beta, ply):
            # time check
            n = nodes[0] + 1
            nodes[0] = n
            if (n & 1023) == 0:
                if time.monotonic() - start > limit:
                    raise Timeout()
            # TT probe
            key = (c, o)
            tt = TT.get(key)
            tt_best = None
            if tt is not None:
                td, ts, tf, tb = tt
                if td >= depth:
                    if tf == 0:
                        return ts
                    elif tf == 1:
                        if ts > alpha:
                            alpha = ts
                    else:
                        if ts < beta:
                            beta = ts
                    if alpha >= beta:
                        return ts
                tt_best = tb

            # generate moves
            mv = []
            mm = c
            while mm:
                lsb = mm & -mm
                s = (lsb.bit_length() - 1)
                for nb in NEIGH[s]:
                    if (o >> nb) & 1:
                        mv.append((s, nb))
                mm ^= lsb
            if not mv:
                return -MATE + ply
            if depth <= 0:
                v = evaluate(c, o)
                # clamp away from mate
                if v >= MATE - 1000:
                    v = MATE - 1001
                if v <= -MATE + 1000:
                    v = -MATE + 1001
                return v

            # order moves
            if tt_best is not None:
                # move tt_best front
                try:
                    mv.remove(tt_best)
                    mv.insert(0, tt_best)
                except Exception:
                    # tt_best not in list, put front if legal (should be legal)
                    pass
                # sort rest by prio
                if len(mv) > 1:
                    first = mv[0]
                    rest = mv[1:]
                    rest.sort(key=lambda x: MOVE_PRIO.get(x, 0), reverse=True)
                    mv = [first] + rest
            else:
                if len(mv) > 1:
                    mv.sort(key=lambda x: MOVE_PRIO.get(x, 0), reverse=True)

            best_score = -INF
            best_mv = mv[0]
            orig_alpha = alpha
            for s, t in mv:
                c_tmp = (c ^ (1 << s)) | (1 << t)
                o_tmp = o ^ (1 << t)
                nc = o_tmp
                no = c_tmp
                sc = -negamax(nc, no, depth - 1, -beta, -alpha, ply + 1)
                if sc > best_score:
                    best_score = sc
                    best_mv = (s, t)
                if sc > alpha:
                    alpha = sc
                if alpha >= beta:
                    break
            # store TT
            if best_score <= orig_alpha:
                flag = 2
            elif best_score >= beta:
                flag = 1
            else:
                flag = 0
            TT[key] = (depth, best_score, flag, best_mv)
            return best_score

        ordered = moves[:]
        # iterative deepening
        for depth in range(1, 31):
            if time.monotonic() - start > limit:
                break
            alpha = -INF
            beta = INF
            cur_best = ordered[0]
            cur_best_score = -INF
            # score each root move to reorder for next iteration
            scored = []
            try:
                for s, t in ordered:
                    c_tmp = (cur ^ (1 << s)) | (1 << t)
                    o_tmp = opp ^ (1 << t)
                    nc = o_tmp
                    no = c_tmp
                    sc = -negamax(nc, no, depth - 1, -beta, -alpha, 1)
                    scored.append((sc, (s, t)))
                    if sc > alpha:
                        alpha = sc
                    if sc > cur_best_score:
                        cur_best_score = sc
                        cur_best = (s, t)
                    # beta is INF at root, no cutoff except exact
                # reorder by score descending for next depth
                scored.sort(key=lambda x: x[0], reverse=True)
                ordered = [m for _, m in scored]
                best = cur_best
                # winning line found
                if cur_best_score >= MATE - 1000:
                    break
                # if depth large enough to solve, break if all lines are mate?
                # continue if time remains
                # heuristic: if branching huge and depth>=3 and time > half, stop to save time?
                # keep going until timeout
                if depth >= 6 and (time.monotonic() - start) > limit * 0.7:
                    break
                if depth >= 3 and len(ordered) > 30 and (time.monotonic() - start) > limit * 0.6:
                    # in opening, don't go too deep
                    # allow one more depth only if fast
                    pass
            except Timeout:
                break
            except Exception:
                break

        s, t = best
        return f"{s//COLS},{s%COLS},{DIRMAP[(s,t)]}"
    except Timeout:
        pass
    except Exception:
        pass
    # emergency fallback: first legal move found by scan
    try:
        cur = board_to_mask(you)
        opp = board_to_mask(opponent)
        mvs = gen_moves_list(cur, opp)
        if mvs:
            s, t = mvs[0]
            return f"{s//COLS},{s%COLS},{DIRMAP[(s,t)]}"
    except Exception:
        pass
    return "0,0,U"
