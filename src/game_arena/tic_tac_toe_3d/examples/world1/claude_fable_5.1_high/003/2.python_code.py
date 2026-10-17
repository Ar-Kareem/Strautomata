
import time

WIN = 100000
INF = 10 ** 9
EXACT, LOWER, UPPER = 0, 1, 2
WEIGHT = (0, 1, 10, 0)


def _idx(i, j, k):
    return i * 9 + j * 3 + k


def _gen_lines():
    lines = set()
    dirs = [(dx, dy, dz) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)
            if (dx, dy, dz) != (0, 0, 0)]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                for dx, dy, dz in dirs:
                    cells = []
                    ok = True
                    for t in range(3):
                        x, y, z = i + t * dx, j + t * dy, k + t * dz
                        if not (0 <= x < 3 and 0 <= y < 3 and 0 <= z < 3):
                            ok = False
                            break
                        cells.append(_idx(x, y, z))
                    if ok:
                        lines.add(tuple(sorted(cells)))
    return tuple(sorted(lines))


LINES = _gen_lines()  # 49 lines
ORDER = [0] * 27
for _a, _b, _c in LINES:
    ORDER[_a] += 1
    ORDER[_b] += 1
    ORDER[_c] += 1

TABLE = []
for _va in (-1, 0, 1):
    for _vb in (-1, 0, 1):
        for _vc in (-1, 0, 1):
            TABLE.append(((_va == 1) + (_vb == 1) + (_vc == 1),
                          (_va == -1) + (_vb == -1) + (_vc == -1)))
TABLE = tuple(TABLE)


class _Timeout(Exception):
    pass


_deadline = 0.0
_nodes = 0
_TT = {}
_root_empties = 0


def _negamax(flat, player, depth, alpha, beta, ply):
    global _nodes
    _nodes += 1
    if (_nodes & 511) == 0 and time.time() > _deadline:
        raise _Timeout()

    if _root_empties - ply <= 0:
        return 0

    key = (tuple(flat), player)
    ent = _TT.get(key)
    tt_move = -1
    if ent is not None:
        d, s, flag, mv = ent
        tt_move = mv
        if d >= depth:
            if flag == EXACT:
                return s
            if flag == LOWER:
                if s > alpha:
                    alpha = s
            else:
                if s < beta:
                    beta = s
            if alpha >= beta:
                return s

    pi = 0 if player == 1 else 1
    oi = 1 - pi
    blocks = None
    score = 0
    tbl = TABLE
    w = WEIGHT
    for a, b, c in LINES:
        va = flat[a]
        vb = flat[b]
        vc = flat[c]
        t = tbl[va * 9 + vb * 3 + vc + 13]
        mine = t[pi]
        theirs = t[oi]
        if theirs == 0:
            if mine == 2:
                return WIN - ply
            score += w[mine]
        elif mine == 0:
            if theirs == 2:
                e = a if va == 0 else (b if vb == 0 else c)
                if blocks is None:
                    blocks = {e}
                else:
                    blocks.add(e)
            score -= w[theirs]

    if blocks is not None:
        if len(blocks) >= 2:
            return -(WIN - ply - 1)
        moves = list(blocks)
    else:
        if depth <= 0:
            return score
        moves = [c for c in range(27) if flat[c] == 0]
        moves.sort(key=lambda c: -ORDER[c])
        if tt_move >= 0 and flat[tt_move] == 0:
            moves.remove(tt_move)
            moves.insert(0, tt_move)

    a0 = alpha
    best = -INF
    bestmove = moves[0]
    for c in moves:
        flat[c] = player
        try:
            s = -_negamax(flat, -player, depth - 1, -beta, -alpha, ply + 1)
        finally:
            flat[c] = 0
        if s > best:
            best = s
            bestmove = c
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    if best <= a0:
        flag = UPPER
    elif best >= beta:
        flag = LOWER
    else:
        flag = EXACT
    _TT[key] = (depth, best, flag, bestmove)
    return best


def _to3(c):
    return (c // 9, (c // 3) % 3, c % 3)


def _wins_at(flat, c, p):
    for a, b, d in LINES:
        if c == a or c == b or c == d:
            cnt = 0
            for x in (a, b, d):
                if x == c or flat[x] == p:
                    cnt += 1
            if cnt == 3:
                return True
    return False


def policy(board):
    global _deadline, _nodes, _TT, _root_empties
    start = time.time()
    flat = [board[i][j][k] for i in range(3) for j in range(3) for k in range(3)]
    empties = [c for c in range(27) if flat[c] == 0]
    if not empties:
        return (0, 0, 0)
    fallback = _to3(max(empties, key=lambda c: ORDER[c]))
    try:
        if len(empties) == 27:
            return (1, 1, 1)
        # immediate win
        for c in empties:
            if _wins_at(flat, c, 1):
                return _to3(c)
        # forced block
        blocks = [c for c in empties if _wins_at(flat, c, -1)]
        if len(blocks) == 1:
            return _to3(blocks[0])
        candidates = blocks if blocks else empties
        candidates = sorted(candidates, key=lambda c: -ORDER[c])

        _deadline = start + 0.55
        _nodes = 0
        _TT = {}
        _root_empties = len(empties)

        best_move = candidates[0]
        depth = 1
        max_depth = len(empties) + 2
        while depth <= max_depth:
            scores = {}
            alpha = -INF
            iter_best = None
            iter_best_score = -INF
            try:
                for c in candidates:
                    flat[c] = 1
                    try:
                        s = -_negamax(flat, -1, depth - 1, -INF, -alpha, 1)
                    finally:
                        flat[c] = 0
                    scores[c] = s
                    if s > iter_best_score:
                        iter_best_score = s
                        iter_best = c
                    if s > alpha:
                        alpha = s
                    if s >= WIN - 50:
                        break
            except _Timeout:
                if iter_best is not None and iter_best_score >= WIN - 50:
                    best_move = iter_best
                break
            best_move = iter_best
            candidates.sort(key=lambda c: -scores.get(c, -INF))
            if abs(iter_best_score) >= WIN - 50:
                break
            depth += 1
            if time.time() > _deadline:
                break
        return _to3(best_move)
    except Exception:
        return fallback
