
# 4x4 Tic-Tac-Toe policy -- alpha-beta engine (win condition: 4 in a row).

import time

TIME_LIMIT = 0.62             # wall-clock seconds per move (hard cap is 1s)
WIN = 1000000                 # ply-adjusted mate score
INF = 10 ** 9
FULL = 0xFFFF

# The 10 winning lines; cell index = 4 * row + col.
LINES = (
    (0, 1, 2, 3), (4, 5, 6, 7), (8, 9, 10, 11), (12, 13, 14, 15),
    (0, 4, 8, 12), (1, 5, 9, 13), (2, 6, 10, 14), (3, 7, 11, 15),
    (0, 5, 10, 15), (3, 6, 9, 12),
)
LINE_MASKS = tuple(sum(1 << i for i in ln) for ln in LINES)

_cl = [[] for _ in range(16)]
for _ln, _lm in zip(LINES, LINE_MASKS):
    for _i in _ln:
        _cl[_i].append(_lm)
CELL_LINES = tuple(tuple(x) for x in _cl)   # lines passing through each cell

POP = bytearray(65536)                      # popcount table for 16-bit masks
for _i in range(1, 65536):
    POP[_i] = POP[_i >> 1] + (_i & 1)

PREF = tuple(4 - int(abs((i >> 2) - 1.5) + abs((i & 3) - 1.5))
             for i in range(16))           # centrality tie-break

W4 = (0, 2, 16, 128, WIN)                   # value of uncontested line with n own stones

TT = {}                                     # (my<<16)|opp -> (depth, flag, score, move)
_deadline = 0.0
_nodes = 0


class _Timeout(Exception):
    pass


def _order_score(c, my, opp):
    """Move-ordering priority for cell c (side to move owns `my`)."""
    sc = 0
    for lm in CELL_LINES[c]:
        m = POP[my & lm]
        if m:
            if not (opp & lm):
                sc += W4[m + 1]             # extends own threat (10^6 => wins now)
        else:
            o = POP[opp & lm]
            if o:
                sc += W4[o]                 # blocks opponent progress
    return sc


def negamax(my, opp, depth, alpha, beta, ply):
    """Negamax alpha-beta. `my` = mask of side to move, `opp` = opponent mask."""
    global _nodes
    _nodes += 1
    if not (_nodes & 511) and time.perf_counter() > _deadline:
        raise _Timeout

    cells = ~(my | opp) & FULL
    if not cells:
        return 0                            # board full: draw

    if depth <= 0:
        # Leaf: tactical extension -- side to move may have an immediate win.
        s = 0
        for lm in LINE_MASKS:
            m = POP[my & lm]
            if m:
                if not (opp & lm):
                    if m == 3:
                        return WIN - ply    # win available right now
                    s += W4[m]
            else:
                o = POP[opp & lm]
                if o:
                    s -= W4[o]
        return s

    key = (my << 16) | opp
    tt_move = -1
    if depth >= 2:
        e = TT.get(key)
        if e is not None:
            ed, ef, es, emv = e
            tt_move = emv
            if ed >= depth:
                if ef == 0:
                    return es
                if ef == 1:
                    if es >= beta:
                        return es
                    if es > alpha:
                        alpha = es
                else:
                    if es <= alpha:
                        return es
                    if es < beta:
                        beta = es

    # Generate and order moves (wins first, then TT move, then threats).
    lst = []
    t = cells
    while t:
        b = t & (-t)
        t ^= b
        c = b.bit_length() - 1
        sc = PREF[c]
        for lm in CELL_LINES[c]:
            m = POP[my & lm]
            if m:
                if not (opp & lm):
                    sc += W4[m + 1]
            else:
                o = POP[opp & lm]
                if o:
                    sc += W4[o]
        if c == tt_move:
            sc += 100000
        lst.append((sc, c))
    lst.sort(reverse=True)

    best = -INF
    best_move = -1
    orig_alpha = alpha
    for sc, c in lst:
        if sc > 500000:                     # flagged by ordering as an immediate win
            best = WIN - ply
            best_move = c
            break                           # cannot do better than winning now
        score = -negamax(opp, my | (1 << c), depth - 1, -beta, -alpha, ply + 1)
        if score > best:
            best = score
            best_move = c
            if score > alpha:
                alpha = score
                if alpha >= beta:
                    break

    if depth >= 2 and -999000 < best < 999000:   # don't store ply-dependent mate scores
        if best >= beta:
            fl = 1                          # lower bound
        elif best > orig_alpha:
            fl = 0                          # exact
        else:
            fl = 2                          # upper bound
        TT[key] = (depth, fl, best, best_move)
    return best


def _search_root(my, opp, cells, empties):
    root = []
    t = cells
    while t:
        b = t & (-t)
        t ^= b
        c = b.bit_length() - 1
        root.append((_order_score(c, my, opp), c))
    if not root:
        return -1
    root.sort(reverse=True)

    prev = {}
    for s, c in root:
        prev[c] = s * 64
    best_move = root[0][1]

    d = 2
    max_d = empties                          # depth == empties => exact solve
    while d <= max_d:
        order = sorted(root, key=lambda mc: -prev[mc[1]])
        cur_move = None
        cur_score = -INF
        alpha = -INF
        try:
            for _s, c in order:
                nm = my | (1 << c)
                won = False
                for lm in CELL_LINES[c]:
                    if (nm & lm) == lm:
                        won = True
                        break
                if won:
                    score = WIN
                else:
                    score = -negamax(opp, nm, d - 1, -INF, -alpha, 1)
                prev[c] = score
                if score > cur_score:
                    cur_score = score
                    cur_move = c
                if score > alpha:
                    alpha = score
        except _Timeout:
            if cur_move is not None:         # trust partial deeper results
                best_move = cur_move
            break
        best_move = cur_move
        if cur_score >= WIN - 1000:          # forced win proven: stop early
            break
        d += 1
    return best_move


def _think(board):
    global _deadline, _nodes
    start = time.perf_counter()
    _deadline = start + TIME_LIMIT
    _nodes = 0

    my = 0
    opp = 0
    for r in range(4):
        row = board[r]
        for c in range(4):
            v = row[c]
            if v == 1:
                my |= 1 << (4 * r + c)
            elif v == -1:
                opp |= 1 << (4 * r + c)

    cells = ~(my | opp) & FULL
    if not cells:
        return (0, 0)

    if my == 0 and opp == 0:
        return (1, 1)                       # opening: take a centre cell

    # 1) Win immediately.
    t = cells
    while t:
        b = t & (-t)
        t ^= b
        c = b.bit_length() - 1
        nm = my | b
        for lm in CELL_LINES[c]:
            if (nm & lm) == lm:
                return (c >> 2, c & 3)

    # 2) Block an immediate opponent win (forced).
    threats = []
    t = cells
    while t:
        b = t & (-t)
        t ^= b
        c = b.bit_length() - 1
        no = opp | b
        for lm in CELL_LINES[c]:
            if (no & lm) == lm:
                threats.append(c)
                break
    if threats:
        if len(threats) == 1:
            c = threats[0]
        else:                               # double threat: block the most useful one
            c = max(threats, key=lambda x: (_order_score(x, my, opp), PREF[x]))
        return (c >> 2, c & 3)

    if len(TT) > 250000:
        TT.clear()

    mv = _search_root(my, opp, cells, POP[cells])
    if mv < 0 or not ((cells >> mv) & 1):   # safety: must be an empty cell
        b = cells & (-cells)
        mv = b.bit_length() - 1
    return (mv >> 2, mv & 3)


def _win4(b, p):
    for i in range(4):
        if b[i][0] == p and b[i][1] == p and b[i][2] == p and b[i][3] == p:
            return True
        if b[0][i] == p and b[1][i] == p and b[2][i] == p and b[3][i] == p:
            return True
    if b[0][0] == p and b[1][1] == p and b[2][2] == p and b[3][3] == p:
        return True
    if b[0][3] == p and b[1][2] == p and b[2][1] == p and b[3][0] == p:
        return True
    return False


def _fallback(board):
    empt = [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]
    if not empt:
        return (0, 0)
    for r, c in empt:
        b2 = [list(row) for row in board]
        b2[r][c] = 1
        if _win4(b2, 1):
            return (r, c)
    for r, c in empt:
        b2 = [list(row) for row in board]
        b2[r][c] = -1
        if _win4(b2, -1):
            return (r, c)
    empt.sort(key=lambda p: (abs(p[0] - 1.5) + abs(p[1] - 1.5), p[0], p[1]))
    return empt[0]


def policy(board):
    # Main engine.
    try:
        r, c = _think(board)
        if 0 <= r <= 3 and 0 <= c <= 3 and board[r][c] == 0:
            return (r, c)
    except Exception:
        pass
    # Simple fallback: win / block / centre.
    try:
        r, c = _fallback(board)
        if 0 <= r <= 3 and 0 <= c <= 3 and board[r][c] == 0:
            return (r, c)
    except Exception:
        pass
    # Last resort: first empty cell.
    try:
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    return (r, c)
    except Exception:
        pass
    return (0, 0)
