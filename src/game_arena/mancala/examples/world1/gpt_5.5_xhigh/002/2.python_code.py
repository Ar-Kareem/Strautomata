
from __future__ import annotations

import sys
import time

sys.setrecursionlimit(10000)

_INF = 10 ** 30
_WIN = 1_000_000

# Keep a safety margin under the 1 second limit.
_TIME_LIMIT = 0.90

# Exact search is useful late, but should remain safe.
_ENDGAME_LIMIT = 10

_TT_LIMIT = 180_000
_ETT_LIMIT = 80_000

_EXACT = 0
_LOWER = 1
_UPPER = 2

_TT = {}
_ETT = {}
_HISTORY = [0, 0, 0, 0, 0, 0]
_KILLERS = {}

_deadline = 0.0
_nodes = 0


class _Timeout(Exception):
    pass


def _house_sum(a):
    return a[0] + a[1] + a[2] + a[3] + a[4] + a[5]


def _weighted(a):
    # Higher indices are closer to our store.
    return a[0] + 2 * a[1] + 3 * a[2] + 4 * a[3] + 5 * a[4] + 6 * a[5]


def _final_value_from_sums(y, o, sy, so):
    diff = (y[6] + sy) - (o[6] + so)
    return diff * _WIN + diff


def _final_value(y, o):
    return _final_value_from_sums(y, o, _house_sum(y), _house_sum(o))


def _rem_hits(start, r, pos):
    """True if the r remainder stones, starting after start, hit cycle position pos."""
    if r <= 0:
        return False
    d = pos - start
    if d <= 0:
        d += 13
    return d <= r


def _play(y, o, m):
    """
    Play legal move m for side y.
    Returns: new_y, new_o, extra_turn, terminal, captured_amount, store_gain.
    """
    n = y[m]
    yl = list(y)
    ol = list(o)
    yl[m] = 0

    q, r = divmod(n, 13)

    if q:
        for i in range(7):
            yl[i] += q
        for i in range(6):
            ol[i] += q

    idx = m
    for _ in range(r):
        idx += 1
        if idx == 13:
            idx = 0
        if idx <= 6:
            yl[idx] += 1
        else:
            ol[idx - 7] += 1

    last = (m + n) % 13
    captured = 0

    if last < 6 and yl[last] == 1:
        oi = 5 - last
        if ol[oi] > 0:
            captured = ol[oi] + 1
            yl[6] += captured
            yl[last] = 0
            ol[oi] = 0

    extra = last == 6

    sy = yl[0] + yl[1] + yl[2] + yl[3] + yl[4] + yl[5]
    so = ol[0] + ol[1] + ol[2] + ol[3] + ol[4] + ol[5]
    terminal = False

    if sy == 0 or so == 0:
        yl[6] += sy
        ol[6] += so
        yl[0] = yl[1] = yl[2] = yl[3] = yl[4] = yl[5] = 0
        ol[0] = ol[1] = ol[2] = ol[3] = ol[4] = ol[5] = 0
        terminal = True
        extra = False

    gain = yl[6] - y[6]
    return tuple(yl), tuple(ol), extra, terminal, captured, gain


def _capture_amount(a, b, i):
    """Fast estimate/exact immediate capture amount for side a moving pit i."""
    n = a[i]
    if n <= 0:
        return 0

    last = (i + n) % 13
    if last >= 6:
        return 0

    q, r = divmod(n, 13)

    if r == 0:
        # Only exactly one full lap leaves the picked pit with one stone.
        if q != 1:
            return 0
    else:
        # If q > 0 the landing pit already received a full-cycle stone.
        if q != 0:
            return 0
        if a[last] != 0:
            return 0

    oi = 5 - last
    opp = b[oi] + q
    if r and _rem_hits(i, r, 7 + oi):
        opp += 1

    if opp <= 0:
        return 0
    return opp + 1


def _store_gain_sow(a, i):
    n = a[i]
    q, r = divmod(n, 13)
    return q + (1 if _rem_hits(i, r, 6) else 0)


def _side_tactical(a, b):
    legal = 0
    extra = 0
    extra_gain = 0
    best_cap = 0
    cap_sum = 0
    best_gain = 0
    gain_sum = 0
    trap = 0

    for i in range(6):
        s = a[i]
        if s > 0:
            legal += 1
            last = (i + s) % 13

            gain = _store_gain_sow(a, i)
            gain_sum += gain
            if gain > best_gain:
                best_gain = gain

            if last == 6:
                extra += 1
                extra_gain += gain

            cap = _capture_amount(a, b, i)
            if cap:
                cap_sum += cap
                if cap > best_cap:
                    best_cap = cap
        else:
            opp = b[5 - i]
            if opp > 0:
                trap += opp

    return legal, extra, extra_gain, best_cap, cap_sum, best_gain, gain_sum, trap


def _evaluate(y, o):
    sy = _house_sum(y)
    so = _house_sum(o)

    if sy == 0 or so == 0:
        return _final_value_from_sums(y, o, sy, so)

    banked = y[6] + o[6]
    store_w = 130 + min(90, banked * 2)

    score = (y[6] - o[6]) * store_w
    score += (sy - so) * 18
    score += (_weighted(y) - _weighted(o)) * 4

    yt = _side_tactical(y, o)
    ot = _side_tactical(o, y)

    score += (yt[0] - ot[0]) * 6       # mobility
    score += (yt[1] - ot[1]) * 55      # extra-turn options
    score += (yt[2] - ot[2]) * 12      # store gain on extra turns
    score += (yt[3] - ot[3]) * 25      # best capture
    score += (yt[4] - ot[4]) * 6       # all capture chances
    score += (yt[5] - ot[5]) * 10      # best direct store gain
    score += (yt[6] - ot[6]) * 2       # total direct store-gain options
    score += (yt[7] - ot[7]) * 3       # empty-pit capture traps

    return score


def _ordered_children(y, o, tt_move, depth):
    children = []
    killer = _KILLERS.get(depth, -1)

    for m in range(6):
        if y[m] <= 0:
            continue

        y2, o2, extra, terminal, cap, gain = _play(y, o, m)

        score = _HISTORY[m] + m * 32 + gain * 50_000 + cap * 200_000

        if m == tt_move:
            score += 1_000_000_000
        if m == killer:
            score += 500_000

        if terminal:
            tv = _final_value(y2, o2)
            if tv > 0:
                score += 100_000_000 + tv // 100
            elif tv == 0:
                score += 10_000_000
            else:
                score += -100_000_000 + tv // 100
        else:
            if extra:
                score += 5_000_000
            score += (_house_sum(y2) - _house_sum(o2)) * 20

        children.append((score, m, y2, o2, extra, terminal, cap, gain))

    children.sort(key=lambda x: x[0], reverse=True)
    return children


def _search(y, o, depth, alpha, beta):
    global _nodes

    _nodes += 1
    if (_nodes & 1023) == 0 and time.perf_counter() >= _deadline:
        raise _Timeout()

    sy = _house_sum(y)
    so = _house_sum(o)

    if sy == 0 or so == 0:
        return _final_value_from_sums(y, o, sy, so)

    if sy + so <= _ENDGAME_LIMIT:
        return _exact(y, o, alpha, beta)

    if depth <= 0:
        return _evaluate(y, o)

    alpha_orig = alpha
    key = (y, o)
    tt_move = -1

    entry = _TT.get(key)
    if entry is not None:
        ed, val, flag, bm = entry
        tt_move = bm
        if ed >= depth:
            if flag == _EXACT:
                return val
            if flag == _LOWER:
                if val > alpha:
                    alpha = val
            else:
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val

    children = _ordered_children(y, o, tt_move, depth)
    if not children:
        return _final_value_from_sums(y, o, sy, so)

    best = -_INF
    best_move = children[0][1]
    first = True
    cutoff = False

    for _, m, y2, o2, extra, terminal, cap, gain in children:
        if terminal:
            val = _final_value(y2, o2)
        elif first or alpha + 1 >= beta:
            if extra:
                val = _search(y2, o2, depth, alpha, beta)
            else:
                val = -_search(o2, y2, depth - 1, -beta, -alpha)
        else:
            if extra:
                val = _search(y2, o2, depth, alpha, alpha + 1)
                if alpha < val < beta:
                    val = _search(y2, o2, depth, alpha, beta)
            else:
                val = -_search(o2, y2, depth - 1, -alpha - 1, -alpha)
                if alpha < val < beta:
                    val = -_search(o2, y2, depth - 1, -beta, -alpha)

        first = False

        if val > best:
            best = val
            best_move = m

        if val > alpha:
            alpha = val

        if alpha >= beta:
            cutoff = True
            _HISTORY[m] += depth * depth + 1
            _KILLERS[depth] = m
            break

    if cutoff:
        flag = _LOWER
    elif best <= alpha_orig:
        flag = _UPPER
    else:
        flag = _EXACT

    _TT[key] = (depth, best, flag, best_move)
    return best


def _exact(y, o, alpha, beta):
    global _nodes

    _nodes += 1
    if (_nodes & 1023) == 0 and time.perf_counter() >= _deadline:
        raise _Timeout()

    sy = _house_sum(y)
    so = _house_sum(o)

    if sy == 0 or so == 0:
        return _final_value_from_sums(y, o, sy, so)

    alpha_orig = alpha
    key = (y, o)
    tt_move = -1

    entry = _ETT.get(key)
    if entry is not None:
        val, flag, bm = entry
        tt_move = bm
        if flag == _EXACT:
            return val
        if flag == _LOWER:
            if val > alpha:
                alpha = val
        else:
            if val < beta:
                beta = val
        if alpha >= beta:
            return val

    children = _ordered_children(y, o, tt_move, 64)
    if not children:
        return _final_value_from_sums(y, o, sy, so)

    best = -_INF
    best_move = children[0][1]
    first = True
    cutoff = False

    for _, m, y2, o2, extra, terminal, cap, gain in children:
        if terminal:
            val = _final_value(y2, o2)
        elif first or alpha + 1 >= beta:
            if extra:
                val = _exact(y2, o2, alpha, beta)
            else:
                val = -_exact(o2, y2, -beta, -alpha)
        else:
            if extra:
                val = _exact(y2, o2, alpha, alpha + 1)
                if alpha < val < beta:
                    val = _exact(y2, o2, alpha, beta)
            else:
                val = -_exact(o2, y2, -alpha - 1, -alpha)
                if alpha < val < beta:
                    val = -_exact(o2, y2, -beta, -alpha)

        first = False

        if val > best:
            best = val
            best_move = m

        if val > alpha:
            alpha = val

        if alpha >= beta:
            cutoff = True
            _HISTORY[m] += 64
            _KILLERS[64] = m
            break

    if cutoff:
        flag = _LOWER
    elif best <= alpha_orig:
        flag = _UPPER
    else:
        flag = _EXACT

    _ETT[key] = (best, flag, best_move)
    return best


def _root_search(y, o, depth):
    if time.perf_counter() >= _deadline:
        raise _Timeout()

    tt_move = -1
    entry = _TT.get((y, o))
    if entry is not None:
        tt_move = entry[3]

    children = _ordered_children(y, o, tt_move, depth)
    if not children:
        return None, _final_value(y, o)

    alpha = -_INF
    beta = _INF
    best = -_INF
    best_move = children[0][1]
    first = True

    for _, m, y2, o2, extra, terminal, cap, gain in children:
        if terminal:
            val = _final_value(y2, o2)
        elif first:
            if extra:
                val = _search(y2, o2, depth, alpha, beta)
            else:
                val = -_search(o2, y2, depth - 1, -beta, -alpha)
        else:
            if extra:
                val = _search(y2, o2, depth, alpha, alpha + 1)
                if alpha < val < beta:
                    val = _search(y2, o2, depth, alpha, beta)
            else:
                val = -_search(o2, y2, depth - 1, -alpha - 1, -alpha)
                if alpha < val < beta:
                    val = -_search(o2, y2, depth - 1, -beta, -alpha)

        first = False

        if val > best:
            best = val
            best_move = m

        if val > alpha:
            alpha = val

    _TT[(y, o)] = (depth, best, _EXACT, best_move)
    return best_move, best


def _book_move(y, o):
    # Standard opening: pit 2 gives an immediate extra turn.
    if y == (4, 4, 4, 4, 4, 4, 0) and o == (4, 4, 4, 4, 4, 4, 0):
        return 2
    return None


def _fallback(y, o):
    legal = [i for i in range(6) if y[i] > 0]
    if not legal:
        return 0

    best_move = legal[0]
    best_val = -_INF

    for m in legal:
        y2, o2, extra, terminal, cap, gain = _play(y, o, m)

        if terminal:
            val = _final_value(y2, o2)
        elif extra:
            val = _evaluate(y2, o2) + 400
        else:
            val = -_evaluate(o2, y2)

        val += gain * 40 + cap * 100 + (400 if extra else 0)

        if val > best_val:
            best_val = val
            best_move = m

    return best_move


def policy(you: list[int], opponent: list[int]) -> int:
    global _deadline, _nodes

    y = tuple(int(v) for v in you)
    o = tuple(int(v) for v in opponent)

    legal = [i for i in range(6) if y[i] > 0]
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]

    if len(_TT) > _TT_LIMIT:
        _TT.clear()
    if len(_ETT) > _ETT_LIMIT:
        _ETT.clear()

    if max(_HISTORY) > 10_000_000:
        for i in range(6):
            _HISTORY[i] //= 2

    _deadline = time.perf_counter() + _TIME_LIMIT
    _nodes = 0

    book = _book_move(y, o)
    if book is not None and y[book] > 0:
        best = book
    else:
        best = _fallback(y, o)

    try:
        for depth in range(1, 65):
            move, val = _root_search(y, o, depth)
            if move is not None and 0 <= move <= 5 and y[move] > 0:
                best = move

            if time.perf_counter() >= _deadline - 0.015:
                break
    except _Timeout:
        pass
    except Exception:
        # Never risk returning an illegal move because of an unexpected issue.
        best = _fallback(y, o)

    if not (0 <= best <= 5) or y[best] <= 0:
        best = legal[0]

    return int(best)
