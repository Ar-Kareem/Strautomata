
import time

INF = 10**9
WIN = 1_000_000

TIME_LIMIT = 0.90
MAX_DEPTH = 64
EXACT_SEED_LIMIT = 14
MAX_TT_SIZE = 350_000

EXACT_FLAG = 0
LOWER_FLAG = 1
UPPER_FLAG = 2

_TT = {}
_EXACT_TT = {}
_DEADLINE = 0.0
_NODE_COUNT = 0


class _Timeout(Exception):
    pass


_PATHS = []
_LAST_POS = []
for _m in range(6):
    _path = []
    for _j in range(_m + 1, 6):
        _path.append((0, _j))
    _path.append((0, 6))
    for _j in range(6):
        _path.append((1, _j))
    for _j in range(0, _m + 1):
        _path.append((0, _j))
    _PATHS.append(_path)

    _last = []
    for _r in range(13):
        _last.append(_path[12] if _r == 0 else _path[_r - 1])
    _LAST_POS.append(_last)


def _check_time():
    global _NODE_COUNT
    _NODE_COUNT += 1
    if (_NODE_COUNT & 2047) == 0 and time.perf_counter() > _DEADLINE:
        raise _Timeout()


def _sum6(s):
    return s[0] + s[1] + s[2] + s[3] + s[4] + s[5]


def _score_margin(margin):
    if margin > 0:
        return WIN + margin * 1000
    if margin < 0:
        return -WIN + margin * 1000
    return 0


def _terminal_score(a, b):
    sa = _sum6(a)
    sb = _sum6(b)
    if sa == 0 or sb == 0:
        return _score_margin((a[6] + sa) - (b[6] + sb))
    return None


def _make_move(a, b, m):
    al = list(a)
    bl = list(b)

    n = al[m]
    al[m] = 0

    q, r = divmod(n, 13)
    path = _PATHS[m]

    if q:
        for side, idx in path:
            if side:
                bl[idx] += q
            else:
                al[idx] += q

    if r:
        for k in range(r):
            side, idx = path[k]
            if side:
                bl[idx] += 1
            else:
                al[idx] += 1

    last_side, last_idx = _LAST_POS[m][r]

    if last_side == 0 and last_idx < 6 and al[last_idx] == 1:
        opp_idx = 5 - last_idx
        if bl[opp_idx] > 0:
            al[6] += bl[opp_idx] + 1
            al[last_idx] = 0
            bl[opp_idx] = 0

    sa = _sum6(al)
    sb = _sum6(bl)

    if sa == 0 or sb == 0:
        if sa:
            al[6] += sa
            for i in range(6):
                al[i] = 0
        if sb:
            bl[6] += sb
            for i in range(6):
                bl[i] = 0
        return tuple(al), tuple(bl), False, _score_margin(al[6] - bl[6])

    extra = last_side == 0 and last_idx == 6
    return tuple(al), tuple(bl), extra, None


def _quick_tactical(a, b):
    best = 0

    for i in range(6):
        n = a[i]
        if n <= 0:
            continue

        q, r = divmod(n, 13)

        gain = q
        if r > (5 - i):
            gain += 1

        last_side, last_idx = _LAST_POS[i][r]
        capture = 0

        if last_side == 0 and last_idx < 6:
            base = 0 if last_idx == i else a[last_idx]
            after_landing = base + q + (1 if r != 0 else 0)

            if after_landing == 1:
                opp_idx = 5 - last_idx
                opp_path_index = 6 - i + opp_idx
                opp_after = b[opp_idx] + q + (1 if r > opp_path_index else 0)

                if opp_after > 0:
                    capture = opp_after + 1
                    gain += capture

        extra = 1 if last_side == 0 and last_idx == 6 else 0
        val = gain * 8 + capture * 10 + extra * 15 + i

        if val > best:
            best = val

    return best


def _evaluate(a, b):
    tv = _terminal_score(a, b)
    if tv is not None:
        return tv

    score = (a[6] - b[6]) * 1000

    asum = 0
    bsum = 0
    apos = 0
    bpos = 0
    a_extra = 0
    b_extra = 0
    a_legal = 0
    b_legal = 0
    a_targets = 0
    b_targets = 0

    for i in range(6):
        ai = a[i]
        bi = b[i]

        asum += ai
        bsum += bi
        apos += ai * (i + 1)
        bpos += bi * (i + 1)

        if ai > 0:
            a_legal += 1
            if (ai - (6 - i)) % 13 == 0:
                a_extra += 1

        if bi > 0:
            b_legal += 1
            if (bi - (6 - i)) % 13 == 0:
                b_extra += 1

        if ai == 0 and b[5 - i] > 0:
            a_targets += b[5 - i] + 1
        if bi == 0 and a[5 - i] > 0:
            b_targets += a[5 - i] + 1

    score += (asum - bsum) * 15
    score += (apos - bpos) * 8
    score += (a_extra - b_extra) * 170
    score += (a_legal - b_legal) * 20
    score += (a_targets - b_targets) * 18
    score += (_quick_tactical(a, b) - _quick_tactical(b, a)) * 12

    score += 25
    return int(score)


def _ordered_children(a, b, preferred=None):
    children = []

    for m in range(6):
        if a[m] <= 0:
            continue

        na, nb, extra, term = _make_move(a, b, m)

        gain = na[6] - a[6]
        order = gain * 10000 + m * 10

        if extra:
            order += 500000

        if term is not None:
            order += term

        if preferred == m:
            order += 2_000_000

        children.append((order, m, na, nb, extra, term))

    children.sort(key=lambda x: x[0], reverse=True)
    return children


def _exact(a, b, alpha, beta):
    _check_time()

    tv = _terminal_score(a, b)
    if tv is not None:
        return tv

    alpha_orig = alpha
    key = a + b
    preferred = None

    ent = _EXACT_TT.get(key)
    if ent is not None:
        val, flag, move = ent
        preferred = move

        if flag == EXACT_FLAG:
            return val
        if flag == LOWER_FLAG and val > alpha:
            alpha = val
        elif flag == UPPER_FLAG and val < beta:
            beta = val

        if alpha >= beta:
            return val

    best = -INF
    best_move = None

    for _, m, na, nb, extra, term in _ordered_children(a, b, preferred):
        if term is not None:
            val = term
        elif extra:
            val = _exact(na, nb, alpha, beta)
        else:
            val = -_exact(nb, na, -beta, -alpha)

        if val > best:
            best = val
            best_move = m

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best_move is None:
        best = _terminal_score(a, b)
        if best is None:
            best = _evaluate(a, b)

    if best <= alpha_orig:
        flag = UPPER_FLAG
    elif best >= beta:
        flag = LOWER_FLAG
    else:
        flag = EXACT_FLAG

    _EXACT_TT[key] = (best, flag, best_move)
    return best


def _negamax(a, b, depth, alpha, beta):
    _check_time()

    tv = _terminal_score(a, b)
    if tv is not None:
        return tv

    if _sum6(a) + _sum6(b) <= EXACT_SEED_LIMIT:
        return _exact(a, b, alpha, beta)

    if depth <= 0:
        return _evaluate(a, b)

    alpha_orig = alpha
    key = a + b
    preferred = None

    ent = _TT.get(key)
    if ent is not None:
        ent_depth, val, flag, move = ent
        preferred = move

        if ent_depth >= depth:
            if flag == EXACT_FLAG:
                return val
            if flag == LOWER_FLAG and val > alpha:
                alpha = val
            elif flag == UPPER_FLAG and val < beta:
                beta = val

            if alpha >= beta:
                return val

    best = -INF
    best_move = None

    for _, m, na, nb, extra, term in _ordered_children(a, b, preferred):
        if term is not None:
            val = term
        elif extra:
            val = _negamax(na, nb, depth - 1, alpha, beta)
        else:
            val = -_negamax(nb, na, depth - 1, -beta, -alpha)

        if val > best:
            best = val
            best_move = m

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best_move is None:
        best = _evaluate(a, b)

    if best <= alpha_orig:
        flag = UPPER_FLAG
    elif best >= beta:
        flag = LOWER_FLAG
    else:
        flag = EXACT_FLAG

    _TT[key] = (depth, best, flag, best_move)
    return best


def _root_search(a, b, depth):
    _check_time()

    key = a + b
    ent = _TT.get(key)
    preferred = ent[3] if ent is not None else None

    alpha = -INF
    beta = INF
    best = -INF
    best_move = None

    for _, m, na, nb, extra, term in _ordered_children(a, b, preferred):
        _check_time()

        if term is not None:
            val = term
        elif extra:
            val = _negamax(na, nb, depth - 1, alpha, beta)
        else:
            val = -_negamax(nb, na, depth - 1, -beta, -alpha)

        if val > best:
            best = val
            best_move = m

        if val > alpha:
            alpha = val

    if best_move is not None:
        _TT[key] = (depth, best, EXACT_FLAG, best_move)

    return best, best_move


def _heuristic_best_move(a, b):
    best_move = None
    best_val = -INF

    for m in range(6):
        if a[m] <= 0:
            continue

        na, nb, extra, term = _make_move(a, b, m)

        if term is not None:
            val = term
        elif extra:
            val = _evaluate(na, nb) + 400
        else:
            val = -_evaluate(nb, na)

        val += (na[6] - a[6]) * 80

        if val > best_val:
            best_val = val
            best_move = m

    if best_move is None:
        for i in range(6):
            if a[i] > 0:
                return i
        return 0

    return best_move


def policy(you: list[int], opponent: list[int]) -> int:
    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return 0

    fallback = legal[0]

    try:
        a = tuple(int(you[i]) for i in range(7))
        b = tuple(int(opponent[i]) for i in range(7))

        fallback = _heuristic_best_move(a, b)

        if len(legal) == 1:
            return int(fallback)

        immediate_win_move = None
        immediate_win_score = -INF
        for m in legal:
            _, _, _, term = _make_move(a, b, m)
            if term is not None and term > immediate_win_score:
                immediate_win_score = term
                immediate_win_move = m

        if immediate_win_move is not None and immediate_win_score > 0:
            return int(immediate_win_move)

        global _DEADLINE, _NODE_COUNT

        _DEADLINE = time.perf_counter() + TIME_LIMIT
        _NODE_COUNT = 0

        if len(_TT) > MAX_TT_SIZE:
            _TT.clear()
        if len(_EXACT_TT) > MAX_TT_SIZE:
            _EXACT_TT.clear()

        best = fallback

        for depth in range(1, MAX_DEPTH + 1):
            if time.perf_counter() > _DEADLINE - 0.005:
                break

            try:
                _, move = _root_search(a, b, depth)
            except _Timeout:
                break

            if move is not None and 0 <= move <= 5 and a[move] > 0:
                best = move

        if 0 <= best <= 5 and a[best] > 0:
            return int(best)

        if 0 <= fallback <= 5 and a[fallback] > 0:
            return int(fallback)

        return int(legal[0])

    except Exception:
        return int(fallback)
