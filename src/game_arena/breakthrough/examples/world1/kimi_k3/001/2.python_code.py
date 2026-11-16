
import time

MATE = 1000000
INF = 2000000
EXACT, LOWER, UPPER = 0, 1, 2


def _precompute():
    WBASE = [0] * 64
    BBASE = [0] * 64
    WDEF = [None] * 64
    WATK = [None] * 64
    BDEF = [None] * 64
    BATK = [None] * 64
    WPATH = [None] * 64
    BPATH = [None] * 64
    MT_W = [None] * 64
    MT_B = [None] * 64
    for r in range(8):
        for c in range(8):
            i = r * 8 + c
            edge = 6 if (c == 0 or c == 7) else 0
            WBASE[i] = 100 + 4 * r + 2 * r * r + edge
            advb = 7 - r
            BBASE[i] = 100 + 4 * advb + 2 * advb * advb + edge

            wd = []
            wa = []
            wp = []
            if r > 0:
                if c > 0:
                    wd.append(i - 9)
                if c < 7:
                    wd.append(i - 7)
            if r < 7:
                if c > 0:
                    wa.append(i + 7)
                    wp.append(i + 7)
                if c < 7:
                    wa.append(i + 9)
                    wp.append(i + 9)
                wp.append(i + 8)
            WDEF[i] = wd
            WATK[i] = wa
            WPATH[i] = wp

            bd = []
            ba = []
            bp = []
            if r < 7:
                if c > 0:
                    bd.append(i + 7)
                if c < 7:
                    bd.append(i + 9)
            if r > 0:
                if c > 0:
                    ba.append(i - 9)
                    bp.append(i - 9)
                if c < 7:
                    ba.append(i - 7)
                    bp.append(i - 7)
                bp.append(i - 8)
            BDEF[i] = bd
            BATK[i] = ba
            BPATH[i] = bp

            MT_W[i] = ((i + 8) if r < 7 else -1,
                       (i + 7) if (r < 7 and c > 0) else -1,
                       (i + 9) if (r < 7 and c < 7) else -1)
            MT_B[i] = ((i - 8) if r > 0 else -1,
                       (i - 9) if (r > 0 and c > 0) else -1,
                       (i - 7) if (r > 0 and c < 7) else -1)
    return WBASE, BBASE, WDEF, WATK, BDEF, BATK, WPATH, BPATH, MT_W, MT_B


(WBASE, BBASE, WDEF, WATK, BDEF, BATK,
 WPATH, BPATH, MT_W, MT_B) = _precompute()

nodes = 0
deadline = 0.0
tt = {}


class _Timeout(Exception):
    pass


def gen_moves(board, color, opp):
    moves = []
    MT = MT_W if color == 1 else MT_B
    for i in range(64):
        if board[i] == color:
            s, dl, dr = MT[i]
            if s >= 0 and board[s] == 0:
                moves.append((i, s))
            if dl >= 0:
                t = board[dl]
                if t == 0 or t == opp:
                    moves.append((i, dl))
            if dr >= 0:
                t = board[dr]
                if t == 0 or t == opp:
                    moves.append((i, dr))
    return moves


def move_score(board, m, color):
    f, t = m
    tgt = board[t]
    r2 = t >> 3
    if tgt != 0:
        adv = r2 if tgt == 1 else 7 - r2
        s = 1000 + 30 * adv
    else:
        s = 0
    s += r2 if color == 1 else 7 - r2
    return s


def evaluate(board, color):
    s = 0
    if color == 2:
        hang_w = 55
        hang_b = 35
    else:
        hang_w = 35
        hang_b = 55
    for i in range(64):
        v = board[i]
        if v == 1:
            val = WBASE[i]
            defended = False
            for d in WDEF[i]:
                if board[d] == 1:
                    defended = True
                    break
            attacked = False
            for a in WATK[i]:
                if board[a] == 2:
                    attacked = True
                    break
            if defended:
                val += 12
            if attacked:
                val -= 10 if defended else hang_w
            else:
                clear = True
                for p in WPATH[i]:
                    if board[p] == 2:
                        clear = False
                        break
                if clear:
                    val += 6
            s += val
        elif v == 2:
            val = BBASE[i]
            defended = False
            for d in BDEF[i]:
                if board[d] == 2:
                    defended = True
                    break
            attacked = False
            for a in BATK[i]:
                if board[a] == 1:
                    attacked = True
                    break
            if defended:
                val += 12
            if attacked:
                val -= 10 if defended else hang_b
            else:
                clear = True
                for p in BPATH[i]:
                    if board[p] == 1:
                        clear = False
                        break
                if clear:
                    val += 6
            s -= val
    return s


def negamax(board, color, depth, alpha, beta, ply, n1, n2):
    global nodes
    nodes += 1
    if (nodes & 1023) == 0 and time.time() > deadline:
        raise _Timeout()

    opp = 3 - color

    # Terminal test: the side that just moved (opp) may have won.
    if opp == 1:
        for j in range(56, 64):
            if board[j] == 1:
                return -MATE + ply
    else:
        for j in range(8):
            if board[j] == 2:
                return -MATE + ply
    if n1 == 0 or n2 == 0:
        return -MATE + ply

    if depth <= 0:
        ev = evaluate(board, color)
        return ev if color == 1 else -ev

    key = (board, color)
    entry = tt.get(key)
    tt_move = None
    if entry is not None:
        ed, esc, efl, emv = entry
        if ed >= depth:
            if efl == EXACT:
                return esc
            elif efl == LOWER:
                if esc > alpha:
                    alpha = esc
            else:
                if esc < beta:
                    beta = esc
            if alpha >= beta:
                return esc
        tt_move = emv

    moves = gen_moves(board, color, opp)
    if not moves:
        return -MATE + ply

    alpha_orig = alpha

    if tt_move is not None and tt_move in moves:
        moves.remove(tt_move)
        moves.sort(key=lambda m: -move_score(board, m, color))
        moves.insert(0, tt_move)
    else:
        moves.sort(key=lambda m: -move_score(board, m, color))

    best = -INF
    best_move = moves[0]
    for idx in range(len(moves)):
        m = moves[idx]
        f, t = m
        captured = board[t]
        b = list(board)
        b[t] = b[f]
        b[f] = 0
        nb = tuple(b)
        if captured == 1:
            cn1 = n1 - 1
            cn2 = n2
        elif captured == 2:
            cn1 = n1
            cn2 = n2 - 1
        else:
            cn1 = n1
            cn2 = n2
        if idx == 0:
            sc = -negamax(nb, opp, depth - 1, -beta, -alpha, ply + 1, cn1, cn2)
        else:
            sc = -negamax(nb, opp, depth - 1, -alpha - 1, -alpha, ply + 1, cn1, cn2)
            if alpha < sc < beta:
                sc = -negamax(nb, opp, depth - 1, -beta, -alpha, ply + 1, cn1, cn2)
        if sc > best:
            best = sc
            best_move = m
        if sc > alpha:
            alpha = sc
            if alpha >= beta:
                break

    if best <= alpha_orig:
        efl = UPPER
    elif best >= beta:
        efl = LOWER
    else:
        efl = EXACT
    tt[key] = (depth, best, efl, best_move)
    return best


def search_root(board, color, depth, n1, n2, prev_best):
    opp = 3 - color
    moves = gen_moves(board, color, opp)
    moves.sort(key=lambda m: -move_score(board, m, color))
    if prev_best is not None and prev_best in moves:
        moves.remove(prev_best)
        moves.insert(0, prev_best)
    alpha = -INF
    best = None
    for m in moves:
        f, t = m
        captured = board[t]
        b = list(board)
        b[t] = b[f]
        b[f] = 0
        nb = tuple(b)
        if captured == 1:
            sc = -negamax(nb, opp, depth - 1, -INF, -alpha, 1, n1 - 1, n2)
        elif captured == 2:
            sc = -negamax(nb, opp, depth - 1, -INF, -alpha, 1, n1, n2 - 1)
        else:
            sc = -negamax(nb, opp, depth - 1, -INF, -alpha, 1, n1, n2)
        if sc > alpha:
            alpha = sc
            best = m
    if best is None:
        best = moves[0]
    return best


def policy(me, opp, color):
    global nodes, deadline, tt

    my_color = 1 if color == 'w' else 2
    opp_color = 3 - my_color

    b = [0] * 64
    for rc in me:
        b[rc[0] * 8 + rc[1]] = my_color
    for rc in opp:
        b[rc[0] * 8 + rc[1]] = opp_color
    board = tuple(b)

    moves = gen_moves(board, my_color, opp_color)
    if not moves:
        # No legal move exists (lost position); return a placeholder.
        if me:
            p = me[0]
            return ((p[0], p[1]), (p[0], p[1]))
        return ((0, 0), (0, 0))

    start = time.time()
    deadline = start + 0.80
    nodes = 0
    tt = {}

    n1 = 0
    n2 = 0
    for v in b:
        if v == 1:
            n1 += 1
        elif v == 2:
            n2 += 1

    moves.sort(key=lambda m: -move_score(board, m, my_color))
    best = moves[0]

    if len(moves) > 1:
        try:
            depth = 1
            while depth <= 30:
                best = search_root(board, my_color, depth, n1, n2, best)
                if time.time() > deadline:
                    break
                depth += 1
        except _Timeout:
            pass
        except Exception:
            pass

    f, t = best
    return ((f >> 3, f & 7), (t >> 3, t & 7))
