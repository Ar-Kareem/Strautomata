
import time

_WIN = 100000
_NOT_COL0 = 0
_NOT_COL5 = 0
for _r in range(5):
    for _c in range(6):
        if _c != 0:
            _NOT_COL0 |= 1 << (_r * 6 + _c)
        if _c != 5:
            _NOT_COL5 |= 1 << (_r * 6 + _c)

try:
    (1).bit_count()
    def _popcount(x):
        return x.bit_count()
except AttributeError:
    def _popcount(x):
        return bin(x).count('1')

_tt = {}
_nodes = 0
_deadline = 0.0


class _Timeout(Exception):
    pass


def _mob(P, O):
    return (_popcount((P << 1) & O & _NOT_COL0) +
            _popcount((P >> 1) & O & _NOT_COL5) +
            _popcount((P << 6) & O) +
            _popcount((P >> 6) & O))


def _gen(P, O):
    res = []
    d = (P << 1) & O & _NOT_COL0
    while d:
        l = d & -d
        res.append((l >> 1, l))
        d ^= l
    d = (P >> 1) & O & _NOT_COL5
    while d:
        l = d & -d
        res.append((l << 1, l))
        d ^= l
    d = (P << 6) & O
    while d:
        l = d & -d
        res.append((l >> 6, l))
        d ^= l
    d = (P >> 6) & O
    while d:
        l = d & -d
        res.append((l << 6, l))
        d ^= l
    return res


def _search(P, O, depth, alpha, beta, ply):
    global _nodes
    _nodes += 1
    if (_nodes & 255) == 0 and time.perf_counter() > _deadline:
        raise _Timeout()
    moves = _gen(P, O)
    if not moves:
        return -(_WIN - ply)
    if depth <= 0:
        return len(moves) - _mob(O, P)

    key = (P, O)
    ttmove = None
    e = _tt.get(key)
    if e is not None:
        edepth, eflag, evalue, emove = e
        if edepth >= depth:
            if eflag == 0:
                return evalue
            if eflag == 1 and evalue >= beta:
                return evalue
            if eflag == 2 and evalue <= alpha:
                return evalue
        ttmove = emove

    scored = []
    for (s, d) in moves:
        nP = (P ^ s) | d
        nO = O ^ d
        om = _mob(nO, nP)
        if om == 0:
            # opponent has no reply: immediate win
            _tt[key] = (depth, 0, _WIN - ply - 1, (s, d))
            return _WIN - ply - 1
        sc = om - _mob(nP, nO)
        if ttmove is not None and s == ttmove[0] and d == ttmove[1]:
            sc -= 100000
        scored.append((sc, s, d))
    scored.sort()

    if depth == 1:
        best = -10 ** 9
        bestmove = None
        for sc, s, d in scored:
            if sc <= -100000:
                sc += 100000
            v = -sc
            if v > best:
                best = v
                bestmove = (s, d)
        _tt[key] = (depth, 0, best, bestmove)
        return best

    best = -10 ** 9
    bestmove = None
    a0 = alpha
    for sc, s, d in scored:
        nP = (P ^ s) | d
        nO = O ^ d
        v = -_search(nO, nP, depth - 1, -beta, -alpha, ply + 1)
        if v > best:
            best = v
            bestmove = (s, d)
        if v > alpha:
            alpha = v
        if alpha >= beta:
            break
    if best >= beta:
        flag = 1
    elif best <= a0:
        flag = 2
    else:
        flag = 0
    _tt[key] = (depth, flag, best, bestmove)
    return best


def _move_str(s, d):
    b = s.bit_length() - 1
    row, col = divmod(b, 6)
    db = d.bit_length() - 1
    diff = db - b
    if diff == 1:
        dr = 'R'
    elif diff == -1:
        dr = 'L'
    elif diff == 6:
        dr = 'D'
    else:
        dr = 'U'
    return "%d,%d,%s" % (row, col, dr)


def policy(you, opponent):
    global _deadline, _nodes, _tt
    start = time.perf_counter()
    P = 0
    O = 0
    for r in range(5):
        for c in range(6):
            if you[r][c]:
                P |= 1 << (r * 6 + c)
            if opponent[r][c]:
                O |= 1 << (r * 6 + c)
    moves = _gen(P, O)
    if not moves:
        return "0,0,U"
    best_move = moves[0]
    if len(moves) == 1:
        return _move_str(best_move[0], best_move[1])

    try:
        if len(_tt) > 1500000:
            _tt = {}
        _deadline = start + 0.75
        _nodes = 0
        max_depth = _popcount(P) + _popcount(O) + 1

        for depth in range(1, max_depth + 1):
            alpha = -10 ** 9
            beta = 10 ** 9
            cur_best = None
            cur_val = -10 ** 9
            # order root moves
            scored = []
            for (s, d) in moves:
                nP = (P ^ s) | d
                nO = O ^ d
                om = _mob(nO, nP)
                sc = om - _mob(nP, nO)
                if om == 0:
                    sc -= 1000000
                if (s, d) == best_move:
                    sc -= 100000
                scored.append((sc, s, d))
            scored.sort()
            for sc, s, d in scored:
                nP = (P ^ s) | d
                nO = O ^ d
                v = -_search(nO, nP, depth - 1, -beta, -alpha, 1)
                if v > cur_val:
                    cur_val = v
                    cur_best = (s, d)
                if v > alpha:
                    alpha = v
            if cur_best is not None:
                best_move = cur_best
            if cur_val >= _WIN - 200 or cur_val <= -(_WIN - 200):
                break
    except _Timeout:
        pass
    except Exception:
        pass

    # final legality safety check
    if best_move not in moves:
        best_move = moves[0]
    return _move_str(best_move[0], best_move[1])
