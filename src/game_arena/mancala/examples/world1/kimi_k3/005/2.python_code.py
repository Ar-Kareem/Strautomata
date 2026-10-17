
import sys
import time

sys.setrecursionlimit(100000)

_INF = 10 ** 9


class _Timeout(Exception):
    pass


_tt = {}          # transposition table: board -> (depth, value, flag, best_move)
_nodes = 0
_deadline = 0.0
_TT_CAP = 1200000


def _make_move(b, m):
    """Apply move m (0..5) for the side to move.

    Layout b: [my houses 0..5, my store 6, opp houses 7..12, opp store 13].
    Returns (next_board, extra_turn, game_over, terminal_value).
    next_board is from the perspective of the player to move next;
    terminal_value is from the perspective of the player who just moved.
    """
    nb = list(b)
    seeds = nb[m]
    nb[m] = 0
    p = m
    while seeds > 1:
        p += 1
        if p == 13:          # skip opponent's store
            p = 0
        nb[p] += 1
        seeds -= 1
    # last seed
    p += 1
    if p == 13:
        p = 0
    if p == 6:
        nb[6] += 1
        extra = True
    elif p < 6 and nb[p] == 0 and nb[12 - p]:
        # capture: opposite of my house p is opp house (5-p) -> flat index 12-p
        nb[6] += nb[12 - p] + 1
        nb[12 - p] = 0
        extra = False
    else:
        nb[p] += 1
        extra = False
    yh = nb[0] + nb[1] + nb[2] + nb[3] + nb[4] + nb[5]
    oh = nb[7] + nb[8] + nb[9] + nb[10] + nb[11] + nb[12]
    if yh == 0 or oh == 0:   # game ends: sweep remaining seeds into stores
        return None, extra, True, 1000 * (nb[6] + yh - nb[13] - oh)
    if extra:
        return tuple(nb), True, False, 0
    # flip perspective so the opponent becomes "you"
    return (nb[7], nb[8], nb[9], nb[10], nb[11], nb[12], nb[13],
            nb[0], nb[1], nb[2], nb[3], nb[4], nb[5], nb[6]), False, False, 0


def _evaluate(b):
    """Heuristic value from the side-to-move perspective."""
    v = 1000 * (b[6] - b[13]) + 400 * (
        (b[0] + b[1] + b[2] + b[3] + b[4] + b[5]) -
        (b[7] + b[8] + b[9] + b[10] + b[11] + b[12]))
    t = 0
    for i in range(6):
        s = b[i]
        if s:
            L = i + s
            if L == 6:                       # extra move available
                t += 150
            elif L < 6 and b[L] == 0:        # capture available
                o = b[12 - L]
                if o:
                    t += 60 * (o + 1)
    return v + t


def _ordered_moves(b, tt_best):
    """Legal moves ordered: TT best, then extra moves, then captures."""
    ms = []
    ap = ms.append
    for i in range(6):
        s = b[i]
        if s:
            sc = 0
            L = i + s
            if L == 6:
                sc = 500
            elif L < 6 and b[L] == 0 and b[12 - L]:
                sc = 100 + 20 * b[12 - L]
            if i == tt_best:
                sc += 100000
            ap((-sc, i))
    ms.sort()
    return ms


def _negamax(b, depth, alpha, beta):
    global _nodes
    _nodes += 1
    if (_nodes & 1023) == 0 and time.perf_counter() > _deadline:
        raise _Timeout
    alpha0 = alpha
    beta0 = beta
    tt_best = -1
    entry = _tt.get(b)
    if entry is not None:
        ed, ev, ef, eb = entry
        if ed >= depth:
            if ef == 0:
                return ev
            if ef == 1:
                if ev > alpha:
                    alpha = ev
            elif ev < beta:
                beta = ev
            if alpha >= beta:
                return ev
        tt_best = eb
    if depth <= 0:
        return _evaluate(b)
    best = -_INF
    best_m = -1
    mk = _make_move
    ng = _negamax
    for nsc, m in _ordered_moves(b, tt_best):
        nb, extra, over, val = mk(b, m)
        if over:
            v = val
        elif extra:
            v = ng(nb, depth, alpha, beta)        # same depth: free extension
        else:
            v = -ng(nb, depth - 1, -beta, -alpha)
        if v > best:
            best = v
            best_m = m
            if v > alpha:
                alpha = v
                if alpha >= beta:
                    break
    if best <= alpha0:
        f = 2
    elif best >= beta0:
        f = 1
    else:
        f = 0
    if len(_tt) < _TT_CAP:
        _tt[b] = (depth, best, f, best_m)
    return best


def policy(you, opponent):
    global _tt, _nodes, _deadline
    b = tuple(you) + tuple(opponent)
    legal = [i for i in range(6) if b[i] > 0]
    if len(legal) == 1:
        return legal[0]

    _tt = {}
    _nodes = 0
    _deadline = time.perf_counter() + 0.85

    best_move = legal[0]
    try:
        # solid default: best static tactical move (always legal)
        best_move = _ordered_moves(b, -1)[0][1]
        total = 0
        for x in b:
            total += x
        win_val = 1000 * total
        mk = _make_move
        ng = _negamax
        depth = 1
        while depth <= 40:
            alpha = -_INF
            cur_best = -_INF
            cur_move = best_move
            for nsc, m in _ordered_moves(b, best_move):
                nb, extra, over, val = mk(b, m)
                if over:
                    v = val
                elif extra:
                    v = ng(nb, depth, alpha, _INF)
                else:
                    v = -ng(nb, depth - 1, -_INF, -alpha)
                if v > cur_best:
                    cur_best = v
                    cur_move = m
                    if v > alpha:
                        alpha = v
            _tt[b] = (depth, cur_best, 0, cur_move)
            best_move = cur_move       # only commit fully completed iterations
            if cur_best >= win_val or cur_best <= -win_val:
                break                  # maximal margin already proven
            depth += 1
    except _Timeout:
        pass
    except Exception:
        pass
    if best_move not in legal:
        best_move = legal[0]
    return int(best_move)
