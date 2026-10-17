
import time

def _gen_lines():
    lines = []
    dirs = []
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for dk in (-1, 0, 1):
                d = (di, dj, dk)
                if d == (0, 0, 0):
                    continue
                for x in d:
                    if x != 0:
                        if x > 0:
                            dirs.append(d)
                        break
    for i in range(3):
        for j in range(3):
            for k in range(3):
                for (di, dj, dk) in dirs:
                    pts = [(i + t * di, j + t * dj, k + t * dk) for t in range(3)]
                    if all(0 <= a < 3 for p in pts for a in p):
                        lines.append(tuple(p[0] * 9 + p[1] * 3 + p[2] for p in pts))
    return lines

_LINES = _gen_lines()
LINE_MASKS = [(1 << a) | (1 << b) | (1 << c) for a, b, c in _LINES]
FULL = (1 << 27) - 1
POP = {}
for _L in LINE_MASKS:
    _bits = [1 << i for i in range(27) if (_L >> i) & 1]
    for _s in range(8):
        _m = 0
        _cnt = 0
        for _t in range(3):
            if (_s >> _t) & 1:
                _m |= _bits[_t]
                _cnt += 1
        POP[_m] = _cnt
CELL_W = [0] * 27
CELL_LINES = [[] for _ in range(27)]
for _idx, _ln in enumerate(_LINES):
    for _c in _ln:
        CELL_W[_c] += 1
        CELL_LINES[_c].append(LINE_MASKS[_idx])
ORDER = sorted(range(27), key=lambda c: -CELL_W[c])

WIN = 10000
INF = 10 ** 9

class _Timeout(Exception):
    pass

_nodes = 0
_deadline = 0.0
_TT = {}

def _search(mine, theirs, depth, alpha, beta, ply):
    global _nodes
    _nodes += 1
    if (_nodes & 255) == 0 and time.perf_counter() > _deadline:
        raise _Timeout
    score = 0
    threats = 0
    threat_cell = 0
    for L in LINE_MASKS:
        a = mine & L
        b = theirs & L
        if a:
            if b:
                continue
            if POP[a] == 2:
                return WIN - ply
            score += 1
        elif b:
            if POP[b] == 2:
                threats += 1
                threat_cell = L ^ b
                score -= 8
            else:
                score -= 1
    if threats >= 2:
        return -(WIN - ply - 1)
    occ = mine | theirs
    if occ == FULL:
        return 0
    if depth <= 0:
        return score
    key = (mine, theirs)
    tt_move = 0
    entry = _TT.get(key)
    if entry is not None:
        edepth, evalue, eflag, emove = entry
        tt_move = emove
        if edepth >= depth:
            if eflag == 0:
                return evalue
            elif eflag == 1:
                if evalue > alpha:
                    alpha = evalue
            else:
                if evalue < beta:
                    beta = evalue
            if alpha >= beta:
                return evalue
    if threats == 1:
        moves = [threat_cell]
    else:
        empty = FULL & ~occ
        moves = [1 << c for c in ORDER if (empty >> c) & 1]
        if tt_move and tt_move in moves:
            moves.remove(tt_move)
            moves.insert(0, tt_move)
    orig_alpha = alpha
    best = -INF
    best_move = 0
    for b in moves:
        v = -_search(theirs, mine | b, depth - 1, -beta, -alpha, ply + 1)
        if v > best:
            best = v
            best_move = b
        if v > alpha:
            alpha = v
        if alpha >= beta:
            break
    if best <= orig_alpha:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    _TT[key] = (depth, best, flag, best_move)
    return best

def _root(mine, theirs, depth, moves):
    alpha = -INF
    beta = INF
    best = -INF
    best_move = moves[0]
    for c in moves:
        b = 1 << c
        v = -_search(theirs, mine | b, depth - 1, -beta, -alpha, 1)
        if v > best:
            best = v
            best_move = c
        if v > alpha:
            alpha = v
    return best, best_move

def _to_tuple(c):
    return (c // 9, (c // 3) % 3, c % 3)

def policy(board):
    global _nodes, _deadline, _TT
    start = time.perf_counter()
    mine = 0
    theirs = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                v = board[i][j][k]
                c = i * 9 + j * 3 + k
                if v == 1:
                    mine |= 1 << c
                elif v == -1:
                    theirs |= 1 << c
    empty = FULL & ~(mine | theirs)
    if empty == FULL:
        return (1, 1, 1)
    empties = [c for c in ORDER if (empty >> c) & 1]
    if not empties:
        return (0, 0, 0)
    fallback = empties[0]
    # immediate win
    for c in empties:
        b = 1 << c
        for L in CELL_LINES[c]:
            if ((mine | b) & L) == L:
                return _to_tuple(c)
    # blocks
    blocks = []
    for c in empties:
        b = 1 << c
        for L in CELL_LINES[c]:
            if ((theirs | b) & L) == L:
                blocks.append(c)
                break
    if blocks:
        return _to_tuple(blocks[0])
    if len(empties) == 1:
        return _to_tuple(empties[0])
    _TT = {}
    _nodes = 0
    _deadline = start + 0.55
    best = fallback
    moves = list(empties)
    try:
        for d in range(1, len(empties) + 1):
            val, mv = _root(mine, theirs, d, moves)
            best = mv
            if mv in moves:
                moves.remove(mv)
                moves.insert(0, mv)
            if abs(val) >= WIN - 200:
                break
    except _Timeout:
        pass
    except Exception:
        pass
    if not ((empty >> best) & 1):
        best = fallback
    return _to_tuple(best)
