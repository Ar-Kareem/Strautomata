
import time

INF = 10 ** 9
TIME_BUDGET = 0.75

_TT = {}
_nodes = 0


class _Timeout(Exception):
    pass


def _sow(b, side, m):
    """Apply move m for side. Returns (new_board, extra_move, game_over)."""
    nb = b[:]
    base = side * 7
    pos = base + m
    seeds = nb[pos]
    nb[pos] = 0
    opp_store = 13 - base
    my_store = base + 6
    idx = pos
    while seeds > 0:
        idx += 1
        if idx == 14:
            idx = 0
        if idx == opp_store:
            continue
        nb[idx] += 1
        seeds -= 1
    extra = False
    if idx == my_store:
        extra = True
    elif base <= idx < base + 6 and nb[idx] == 1:
        opp_idx = 12 - idx
        if nb[opp_idx] > 0:
            nb[my_store] += nb[opp_idx] + 1
            nb[opp_idx] = 0
            nb[idx] = 0
    s0 = nb[0] + nb[1] + nb[2] + nb[3] + nb[4] + nb[5]
    s1 = nb[7] + nb[8] + nb[9] + nb[10] + nb[11] + nb[12]
    if s0 == 0 or s1 == 0:
        nb[6] += s0
        nb[13] += s1
        for i in range(6):
            nb[i] = 0
            nb[7 + i] = 0
        return nb, False, True
    return nb, extra, False


def _eval(b, side):
    base = side * 7
    ob = 7 - base
    diff = b[base + 6] - b[ob + 6]
    score = 100 * diff
    mine = 0
    theirs = 0
    for i in range(6):
        s = b[base + i]
        mine += s
        if s and s % 13 == 6 - i:
            score += 8
        t = b[ob + i]
        theirs += t
        if t and t % 13 == 6 - i:
            score -= 8
    score += 2 * (mine - theirs)
    return score


def _terminal_value(nb, side):
    base = side * 7
    d = nb[base + 6] - nb[13 - base]
    if d > 0:
        return 100 * d + 10000
    if d < 0:
        return 100 * d - 10000
    return 0


def _search(b, side, depth, alpha, beta, deadline):
    global _nodes
    _nodes += 1
    if (_nodes & 1023) == 0 and time.perf_counter() > deadline:
        raise _Timeout()
    base = side * 7
    key = (tuple(b), side)
    ent = _TT.get(key)
    tt_move = -1
    if ent is not None:
        ed, ev, ef, em = ent
        tt_move = em
        if ed >= depth:
            if ef == 0:
                return ev
            if ef == 1 and ev >= beta:
                return ev
            if ef == 2 and ev <= alpha:
                return ev
    if depth <= 0:
        return _eval(b, side)
    children = []
    for m in range(6):
        if b[base + m] == 0:
            continue
        nb, extra, end = _sow(b, side, m)
        gain = nb[base + 6] - b[base + 6]
        pri = gain + (50 if extra else 0) + (1000 if m == tt_move else 0)
        children.append((pri, m, nb, extra, end))
    if not children:
        return _eval(b, side)
    children.sort(key=lambda x: -x[0])
    best = -INF
    best_m = children[0][1]
    a = alpha
    for pri, m, nb, extra, end in children:
        if end:
            val = _terminal_value(nb, side)
        elif extra:
            val = _search(nb, side, depth, a, beta, deadline)
        else:
            val = -_search(nb, 1 - side, depth - 1, -beta, -a, deadline)
        if val > best:
            best = val
            best_m = m
        if best > a:
            a = best
        if a >= beta:
            break
    if best <= alpha:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    _TT[key] = (depth, best, flag, best_m)
    return best


def policy(you, opponent):
    global _nodes
    start = time.perf_counter()
    deadline = start + TIME_BUDGET
    b = list(you) + list(opponent)
    legal = [m for m in range(6) if b[m] > 0]
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]

    # Heuristic fallback: prefer an extra-move house, else capture, else last house.
    best_move = legal[-1]
    for m in legal:
        if b[m] % 13 == 6 - m:
            best_move = m
            break
    else:
        best_gain = -1
        for m in legal:
            nb, extra, end = _sow(b, 0, m)
            gain = nb[6] - b[6]
            if gain > best_gain:
                best_gain = gain
                best_move = m

    _TT.clear()
    _nodes = 0
    order = list(legal)
    try:
        for depth in range(1, 60):
            # Order root moves: previous best first
            if best_move in order:
                order.remove(best_move)
                order.insert(0, best_move)
            children = []
            for m in order:
                nb, extra, end = _sow(b, 0, m)
                children.append((m, nb, extra, end))
            alpha = -INF
            beta = INF
            cur_best = None
            cur_val = -INF
            for m, nb, extra, end in children:
                if end:
                    val = _terminal_value(nb, 0)
                elif extra:
                    val = _search(nb, 0, depth, alpha, beta, deadline)
                else:
                    val = -_search(nb, 1, depth - 1, -beta, -alpha, deadline)
                if val > cur_val:
                    cur_val = val
                    cur_best = m
                if cur_val > alpha:
                    alpha = cur_val
            if cur_best is not None:
                best_move = cur_best
            # Re-order root moves by results for next iteration
            if abs(cur_val) >= 9000:
                break
            if time.perf_counter() > deadline:
                break
    except _Timeout:
        pass
    except Exception:
        pass

    if best_move < 0 or best_move > 5 or you[best_move] <= 0:
        best_move = legal[0]
    return int(best_move)
