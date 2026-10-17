
import time

_SEED = 1024
_INF = 1 << 60
_TIME_LIMIT = 0.90


class _Timeout(Exception):
    pass


def _final_value(y, o):
    sy = sum(y[:6])
    so = sum(o[:6])
    if sy == 0:
        ytot = y[6]
        otot = o[6] + so
    elif so == 0:
        ytot = y[6] + sy
        otot = o[6]
    else:
        ytot = y[6] + sy
        otot = o[6] + so
    return (ytot - otot) * _SEED


def _apply_move(y, o, i):
    ny = list(y)
    no = list(o)
    n = ny[i]
    ny[i] = 0

    q, r = divmod(n, 13)
    if q:
        for k in range(6):
            ny[k] += q
            no[k] += q
        ny[6] += q

    p = i + r
    if p >= 13:
        p -= 13

    for t in range(1, r + 1):
        pos = i + t
        if pos >= 13:
            pos -= 13
        if pos < 6:
            ny[pos] += 1
        elif pos == 6:
            ny[6] += 1
        else:
            no[pos - 7] += 1

    if p < 6:
        # Seeds already present in the target house before the last drop.
        before = (y[p] + q) if r else (q - 1)
        if before == 0:
            op = 5 - p
            if no[op] > 0:
                captured = ny[p] + no[op]
                ny[6] += captured
                ny[p] = 0
                no[op] = 0

    terminal = (sum(ny[:6]) == 0) or (sum(no[:6]) == 0)
    return tuple(ny), tuple(no), p == 6, terminal


def _extra_and_capture(board, other):
    extras = 0
    best_cap = 0
    for i, c in enumerate(board[:6]):
        if c <= 0:
            continue
        if c % 13 == 6 - i:
            extras += 1

        # Immediate capture is possible only when the landing house is still
        # empty before the last seed. For n > 13 full laps make it non-empty,
        # except the exact n == 13 full-lap landing on the source house.
        if c < 13:
            p = i + c
            if p >= 13:
                p -= 13
            if p < 6 and board[p] == 0:
                gain = 1 + other[5 - p] + (1 if p < i else 0)
                if gain > best_cap:
                    best_cap = gain
        elif c == 13:
            gain = 1 + other[5 - i] + 1
            if gain > best_cap:
                best_cap = gain
    return extras, best_cap


def _quick_eval(y, o):
    sy = sum(y[:6])
    so = sum(o[:6])
    side_diff = y[6] + sy - o[6] - so
    store_diff = y[6] - o[6]

    ey, cy = _extra_and_capture(y, o)
    eo, co = _extra_and_capture(o, y)

    return (
        side_diff * _SEED
        + store_diff * 80
        + (ey - eo) * 44
        + (cy - co) * 14
    )


def _children(y, o):
    out = []
    for i in range(6):
        if y[i] <= 0:
            continue
        ny, no, extra, terminal = _apply_move(y, o, i)
        if terminal:
            est = _final_value(ny, no)
        elif extra:
            est = _quick_eval(ny, no) + 60
        else:
            est = -_quick_eval(no, ny)
        out.append((est, i, ny, no, extra, terminal))
    out.sort(key=lambda x: x[0], reverse=True)
    return out


def _search(y, o, depth, alpha, beta, tt, deadline, nodes):
    nodes[0] += 1
    if (nodes[0] & 511) == 0 and time.perf_counter() >= deadline:
        raise _Timeout

    if sum(y[:6]) == 0 or sum(o[:6]) == 0:
        return _final_value(y, o)
    if depth <= 0:
        return _quick_eval(y, o)

    alpha_orig = alpha
    beta_orig = beta
    key = (y, o, depth)

    entry = tt.get(key)
    tt_best = None
    if entry is not None:
        val, flag, bm = entry
        tt_best = bm
        if flag == 0:
            return val
        if flag == 1 and val > alpha:
            alpha = val
        elif flag == 2 and val < beta:
            beta = val
        if alpha >= beta:
            return val

    children = _children(y, o)
    if not children:
        return _final_value(y, o)
    if tt_best is not None:
        children.sort(key=lambda x: x[1] != tt_best)

    best = -_INF
    best_move = children[0][1]

    for _, move, ny, no, extra, terminal in children:
        if terminal:
            val = _final_value(ny, no)
        elif extra:
            val = _search(ny, no, depth - 1, alpha, beta, tt, deadline, nodes)
        else:
            val = -_search(no, ny, depth - 1, -beta, -alpha, tt, deadline, nodes)

        if val > best:
            best = val
            best_move = move
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    if best <= alpha_orig:
        flag = 2
    elif best >= beta_orig:
        flag = 1
    else:
        flag = 0
    tt[key] = (best, flag, best_move)
    return best


def policy(you: list[int], opponent: list[int]) -> int:
    y = tuple(int(x) for x in you)
    o = tuple(int(x) for x in opponent)

    legal = [i for i in range(6) if y[i] > 0]
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]

    best = legal[0]
    try:
        ch = _children(y, o)
        if ch:
            best = ch[0][1]
    except Exception:
        pass

    deadline = time.perf_counter() + _TIME_LIMIT
    tt = {}
    nodes = [0]

    depth = 1
    while time.perf_counter() < deadline and depth <= 80:
        try:
            _search(y, o, depth, -_INF, _INF, tt, deadline, nodes)
            ent = tt.get((y, o, depth))
            if ent is not None:
                bm = ent[2]
                if bm is not None and 0 <= bm < 6 and y[bm] > 0:
                    best = bm
        except _Timeout:
            break
        except Exception:
            break
        depth += 1

    if best is None or not (0 <= best < 6) or y[best] <= 0:
        best = legal[0]
    return int(best)
