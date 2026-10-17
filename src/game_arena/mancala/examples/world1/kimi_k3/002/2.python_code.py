
import time

_INF = 10 ** 100
_EXACT, _LOWER, _UPPER = 0, 1, 2


class _Timeout(Exception):
    pass


def _swap(pos):
    return pos[7:14] + pos[0:7]


def _apply_move(st, i):
    # st = current player's 6 houses, current store, opponent's 6 houses, opponent store.
    a = list(st)
    n = a[i]
    a[i] = 0

    # Sow around positions 0..12, skipping position 13 (opponent store).
    q, r = divmod(n, 13)
    if q:
        for k in range(13):
            a[k] += q
    p = i
    for _ in range(r):
        p += 1
        if p == 13:
            p = 0
        a[p] += 1

    extra = p == 6
    cap = 0
    if p < 6 and a[p] == 1:
        op = 12 - p  # opponent[5 - p]
        if a[op]:
            cap = a[op] + 1
            a[6] += cap
            a[op] = 0
            a[p] = 0

    sy = a[0] + a[1] + a[2] + a[3] + a[4] + a[5]
    so = a[7] + a[8] + a[9] + a[10] + a[11] + a[12]
    term = sy == 0 or so == 0
    if term:
        if sy == 0 and so:
            a[13] += so
            a[7] = a[8] = a[9] = a[10] = a[11] = a[12] = 0
        if so == 0 and sy:
            a[6] += sy
            a[0] = a[1] = a[2] = a[3] = a[4] = a[5] = 0
    return tuple(a), extra, term, cap


def _positional(st):
    ys = st[0] + st[1] + st[2] + st[3] + st[4] + st[5]
    os = st[7] + st[8] + st[9] + st[10] + st[11] + st[12]
    wy = st[0] + 2 * st[1] + 3 * st[2] + 4 * st[3] + 5 * st[4] + 6 * st[5]
    wo = st[7] + 2 * st[8] + 3 * st[9] + 4 * st[10] + 5 * st[11] + 6 * st[12]
    ny = (st[0] > 0) + (st[1] > 0) + (st[2] > 0) + (st[3] > 0) + (st[4] > 0) + (st[5] > 0)
    no = (st[7] > 0) + (st[8] > 0) + (st[9] > 0) + (st[10] > 0) + (st[11] > 0) + (st[12] > 0)
    return (ys - os) * 6 + (wy - wo) + (ny - no) * 10


def _evaluate(st):
    v = (st[6] - st[13]) * 1000 + _positional(st)
    bonus = 0
    for i in range(6):
        n = st[i]
        if not n:
            continue
        p = (i + n) % 13
        if p == 6:
            bonus += 35
        elif p < 6:
            opp = st[12 - p]
            if opp:
                base = 0 if p == i else st[p]
                m = n - 1
                qm, rm = divmod(m, 13)
                d = p - i - 1
                if d < 0:
                    d += 13
                before = base + qm + (1 if d < rm else 0)
                if before == 0:
                    bonus += 25 + min(opp, 25)
    return v + bonus


def policy(you: list[int], opponent: list[int]) -> int:
    st = tuple(int(v) for v in you) + tuple(int(v) for v in opponent)
    legal = [i for i in range(6) if st[i] > 0]
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]

    clock = time.perf_counter
    deadline = clock() + 0.90
    total = sum(st)
    scale = total * 10000 + 100000
    tt = {}

    def children(pos, tt_best):
        out = []
        for i in range(6):
            if pos[i]:
                c, extra, term, cap = _apply_move(pos, i)
                if term:
                    qv = (c[6] - c[13]) * scale
                else:
                    qv = (c[6] - c[13]) * 1000 + _positional(c) + cap * 150 + (140 if extra else 0)
                out.append((i, c, extra, term, qv))
        out.sort(key=lambda x: (x[0] != tt_best, -x[4]))
        return out

    def search(pos, depth, alpha, beta):
        if clock() > deadline:
            raise _Timeout

        sy = pos[0] + pos[1] + pos[2] + pos[3] + pos[4] + pos[5]
        so = pos[7] + pos[8] + pos[9] + pos[10] + pos[11] + pos[12]
        if sy == 0 or so == 0:
            a = list(pos)
            if sy == 0 and so:
                a[13] += so
                a[7] = a[8] = a[9] = a[10] = a[11] = a[12] = 0
            if so == 0 and sy:
                a[6] += sy
                a[0] = a[1] = a[2] = a[3] = a[4] = a[5] = 0
            return (a[6] - a[13]) * scale

        if depth <= 0:
            return _evaluate(pos)

        e = tt.get(pos)
        tt_best = -1
        if e is not None:
            tt_best = e[3]
            if e[0] >= depth:
                v = e[1]
                f = e[2]
                if f == _EXACT:
                    return v
                if f == _LOWER:
                    if v > alpha:
                        alpha = v
                else:
                    if v < beta:
                        beta = v
                if alpha >= beta:
                    return v

        old_alpha, old_beta = alpha, beta
        best_v = -_INF
        best_m = -1
        for m, c, extra, term, _qv in children(pos, tt_best):
            if term:
                v = (c[6] - c[13]) * scale
            elif extra:
                v = search(c, depth - 1, alpha, beta)
            else:
                v = -search(_swap(c), depth - 1, -beta, -alpha)

            if v > best_v:
                best_v = v
                best_m = m
            if v > alpha:
                alpha = v
            if alpha >= beta:
                break

        if best_v <= old_alpha:
            flag = _UPPER
        elif best_v >= old_beta:
            flag = _LOWER
        else:
            flag = _EXACT
        tt[pos] = (depth, best_v, flag, best_m)
        return best_v

    root = children(st, -1)
    best = root[0][0]
    scores = {m: qv for m, _c, _e, _t, qv in root}
    house_total = sum(st[0:6]) + sum(st[7:13])
    max_depth = 100 if house_total <= 20 else 64

    for depth in range(1, max_depth + 1):
        if clock() > deadline:
            break
        root.sort(key=lambda x: (x[0] != best, -scores.get(x[0], x[4])))
        alpha = -_INF
        beta = _INF
        cur_best = best
        cur_v = -_INF
        try:
            for m, c, extra, term, _qv in root:
                if term:
                    v = (c[6] - c[13]) * scale
                elif extra:
                    v = search(c, depth - 1, alpha, beta)
                else:
                    v = -search(_swap(c), depth - 1, -beta, -alpha)

                scores[m] = v
                if v > cur_v:
                    cur_v = v
                    cur_best = m
                if v > alpha:
                    alpha = v
            best = cur_best
            if all(t[3] for t in root):
                break
        except _Timeout:
            break

    return int(best)
