
import time

_TT = {}
_nodes = 0
_deadline = 0.0
_total = 48


class _Timeout(Exception):
    pass


def _sow(b, p, m):
    b = list(b)
    base = p * 7
    pos = base + m
    seeds = b[pos]
    b[pos] = 0
    own_store = base + 6
    opp_store = 19 - own_store
    if seeds > 13:
        full = (seeds - 1) // 13
        seeds -= full * 13
        for i in range(14):
            b[i] += full
        b[opp_store] -= full
    idx = pos
    while seeds:
        idx += 1
        if idx > 13:
            idx = 0
        if idx == opp_store:
            continue
        b[idx] += 1
        seeds -= 1
    extra = False
    if idx == own_store:
        extra = True
    elif base <= idx < base + 6 and b[idx] == 1:
        opp = 12 - idx
        if b[opp] > 0:
            b[own_store] += b[opp] + 1
            b[opp] = 0
            b[idx] = 0
    s0 = b[0] + b[1] + b[2] + b[3] + b[4] + b[5]
    s1 = b[7] + b[8] + b[9] + b[10] + b[11] + b[12]
    if s0 == 0 or s1 == 0:
        b[6] += s0
        b[13] += s1
        for i in range(6):
            b[i] = 0
            b[7 + i] = 0
        return b, p, True
    return b, (p if extra else 1 - p), False


def _terminal(b, p):
    base = p * 7
    diff = b[base + 6] - b[13 - base]
    if diff > 0:
        return 20000 + diff * 100
    if diff < 0:
        return -20000 + diff * 100
    return 0


def _eval(b, p):
    base = p * 7
    ob = 7 - base
    diff = b[base + 6] - b[13 - base]
    hs = (b[base] + b[base + 1] + b[base + 2] + b[base + 3] + b[base + 4] + b[base + 5]) - \
         (b[ob] + b[ob + 1] + b[ob + 2] + b[ob + 3] + b[ob + 4] + b[ob + 5])
    return diff * 100 + hs * 20


def _search(b, p, depth, alpha, beta):
    global _nodes
    _nodes += 1
    if (_nodes & 127) == 0 and time.perf_counter() > _deadline:
        raise _Timeout()
    base = p * 7
    my_store = b[base + 6]
    op_store = b[13 - base]
    if my_store * 2 > _total:
        return 20000 + (my_store - op_store) * 100
    if op_store * 2 > _total:
        return -20000 + (my_store - op_store) * 100
    if depth <= 0:
        return _eval(b, p)
    key = (tuple(b), p)
    tt = _TT.get(key)
    tt_move = -1
    if tt is not None:
        tdepth, tval, tflag, tmove = tt
        if tdepth >= depth:
            if tflag == 0:
                return tval
            if tflag == 1 and tval >= beta:
                return tval
            if tflag == 2 and tval <= alpha:
                return tval
        tt_move = tmove
    children = []
    for m in range(6):
        if b[base + m] > 0:
            nb, np_, over = _sow(b, p, m)
            if over:
                sc = _terminal(nb, p)
            else:
                sc = (nb[base + 6] - my_store) * 10
                if np_ == p:
                    sc += 1000
            if m == tt_move:
                sc += 100000
            children.append((sc, m, nb, np_, over))
    if not children:
        return _terminal(b, p)
    children.sort(key=lambda c: -c[0])
    orig_alpha = alpha
    best = -10 ** 9
    best_move = children[0][1]
    for sc, m, nb, np_, over in children:
        if over:
            val = _terminal(nb, p)
        elif np_ == p:
            val = _search(nb, p, depth - 1, alpha, beta)
        else:
            val = -_search(nb, np_, depth - 1, -beta, -alpha)
        if val > best:
            best = val
            best_move = m
        if best > alpha:
            alpha = best
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


def policy(you, opponent):
    global _deadline, _nodes, _total
    start = time.perf_counter()
    legal = [m for m in range(6) if you[m] > 0]
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]
    b = list(you) + list(opponent)
    _total = sum(b)
    _deadline = start + 0.65
    _nodes = 0
    _TT.clear()

    # Heuristic fallback and root children
    children = {}
    order = []
    for m in legal:
        nb, np_, over = _sow(b, 0, m)
        if over:
            sc = _terminal(nb, 0)
        else:
            sc = (nb[6] - b[6]) * 10
            if np_ == 0:
                sc += 1000
        children[m] = (nb, np_, over)
        order.append((sc, m))
    order.sort(key=lambda x: -x[0])
    order = [m for _, m in order]
    best_move = order[0]

    try:
        for depth in range(1, 100):
            alpha = -10 ** 9
            beta = 10 ** 9
            scores = {}
            cur_best = None
            cur_val = -10 ** 9
            for m in order:
                nb, np_, over = children[m]
                if over:
                    val = _terminal(nb, 0)
                elif np_ == 0:
                    val = _search(nb, 0, depth - 1, alpha, beta)
                else:
                    val = -_search(nb, 1, depth - 1, -beta, -alpha)
                scores[m] = val
                if val > cur_val:
                    cur_val = val
                    cur_best = m
                    best_move = m
                if val > alpha:
                    alpha = val
            order.sort(key=lambda m: -scores[m])
            best_move = cur_best
            if abs(cur_val) >= 19000:
                break
            if depth >= 2 * _total + 10:
                break
    except _Timeout:
        pass
    except Exception:
        pass

    if best_move is None or best_move < 0 or best_move > 5 or you[best_move] <= 0:
        best_move = legal[0]
    return best_move
