
from time import perf_counter

INF = 10**9
FLAG_UPPER = -1
FLAG_EXACT = 0
FLAG_LOWER = 1

EXACT_TOTAL = 10
EXACT_DEPTH = 10**6

TT_MAX = 400000
EXACT_TT_MAX = 150000

_TT = {}
_EXACT_TT = {}
_DEADLINE = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


def _house_sum(side):
    return side[0] + side[1] + side[2] + side[3] + side[4] + side[5]


def _terminal_value(you, opp, sy=None, so=None):
    if sy is None:
        sy = _house_sum(you)
        so = _house_sum(opp)
    return you[6] + sy - opp[6] - so


def _tick():
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and perf_counter() >= _DEADLINE:
        raise _Timeout


def _apply_move(you, opp, move):
    y = list(you)
    o = list(opp)

    seeds = y[move]
    y[move] = 0
    p = move
    last_side = 0
    last_idx = 0

    while seeds:
        p = (p + 1) % 13
        if p <= 5:
            y[p] += 1
            last_side = 0
            last_idx = p
        elif p == 6:
            y[6] += 1
            last_side = 0
            last_idx = 6
        else:
            j = p - 7
            o[j] += 1
            last_side = 1
            last_idx = j
        seeds -= 1

    extra = last_side == 0 and last_idx == 6

    if last_side == 0 and last_idx <= 5 and y[last_idx] == 1 and o[5 - last_idx] > 0:
        y[6] += 1 + o[5 - last_idx]
        y[last_idx] = 0
        o[5 - last_idx] = 0

    sy = y[0] + y[1] + y[2] + y[3] + y[4] + y[5]
    so = o[0] + o[1] + o[2] + o[3] + o[4] + o[5]
    if sy == 0 or so == 0:
        y[6] += sy
        o[6] += so
        y[0] = y[1] = y[2] = y[3] = y[4] = y[5] = 0
        o[0] = o[1] = o[2] = o[3] = o[4] = o[5] = 0

    return tuple(y), tuple(o), extra


def _move_order_score(you, opp, move):
    s = you[move]
    last = (move + s) % 13
    score = move

    dist_to_store = 6 - move
    if s >= dist_to_store:
        score += 20 * (1 + (s - dist_to_store) // 13)

    if last == 6:
        score += 1000
    elif s <= 13 and last <= 5 and ((last == move) or (you[last] == 0)) and opp[5 - last] > 0:
        score += 200 + 5 * opp[5 - last]

    return score


def _ordered_moves(you, opp, tt_move=None):
    moves = [i for i in range(6) if you[i] > 0]
    if len(moves) <= 1:
        return moves

    if tt_move in moves:
        moves.remove(tt_move)
        moves.sort(key=lambda m: _move_order_score(you, opp, m), reverse=True)
        return [tt_move] + moves

    moves.sort(key=lambda m: _move_order_score(you, opp, m), reverse=True)
    return moves


def _evaluate(you, opp):
    sy = _house_sum(you)
    so = _house_sum(opp)
    if sy == 0 or so == 0:
        return _terminal_value(you, opp, sy, so)

    store_diff = you[6] - opp[6]
    house_diff = sy - so

    # Light preference for seeds closer to the store.
    front_diff = (
        (you[3] - opp[3]) +
        2 * (you[4] - opp[4]) +
        3 * (you[5] - opp[5])
    )

    own_mob = 0
    opp_mob = 0
    own_extra = 0
    opp_extra = 0
    own_cap = 0
    opp_cap = 0

    for i in range(6):
        s = you[i]
        if s > 0:
            own_mob += 1
            last = (i + s) % 13
            if last == 6:
                own_extra += 1
            elif s <= 13 and last <= 5 and ((last == i) or (you[last] == 0)):
                cap = opp[5 - last]
                if cap > 0:
                    cap += 1
                    if cap > own_cap:
                        own_cap = cap

        s = opp[i]
        if s > 0:
            opp_mob += 1
            last = (i + s) % 13
            if last == 6:
                opp_extra += 1
            elif s <= 13 and last <= 5 and ((last == i) or (opp[last] == 0)):
                cap = you[5 - last]
                if cap > 0:
                    cap += 1
                    if cap > opp_cap:
                        opp_cap = cap

    total = sy + so
    race = 0
    if total < 18:
        if store_diff > 0:
            race = so - sy
        elif store_diff < 0:
            race = sy - so

    return (
        24 * store_diff
        + 6 * house_diff
        + front_diff
        + 10 * (own_extra - opp_extra)
        + 4 * (own_cap - opp_cap)
        + 2 * (own_mob - opp_mob)
        + max(0, 18 - total) * race
    )


def _exact(you, opp):
    _tick()

    sy = _house_sum(you)
    so = _house_sum(opp)
    if sy == 0 or so == 0:
        return _terminal_value(you, opp, sy, so)

    key = (you, opp)
    cached = _EXACT_TT.get(key)
    if cached is not None:
        val, best_move = cached
        old = _TT.get(key)
        if old is None or old[0] < EXACT_DEPTH:
            _TT[key] = (EXACT_DEPTH, FLAG_EXACT, val, best_move)
        return val

    tt_entry = _TT.get(key)
    tt_move = tt_entry[3] if tt_entry is not None else None

    best = -INF
    best_move = None

    for m in _ordered_moves(you, opp, tt_move):
        ny, no, extra = _apply_move(you, opp, m)
        if extra:
            val = _exact(ny, no)
        else:
            val = -_exact(no, ny)

        if val > best:
            best = val
            best_move = m

    _EXACT_TT[key] = (best, best_move)
    _TT[key] = (EXACT_DEPTH, FLAG_EXACT, best, best_move)
    return best


def _search(you, opp, depth, alpha, beta):
    _tick()

    sy = _house_sum(you)
    so = _house_sum(opp)
    if sy == 0 or so == 0:
        return _terminal_value(you, opp, sy, so)

    if sy + so <= EXACT_TOTAL:
        return _exact(you, opp)

    if depth <= 0:
        return _evaluate(you, opp)

    key = (you, opp)
    alpha_orig = alpha
    beta_orig = beta

    tt_entry = _TT.get(key)
    tt_move = None
    if tt_entry is not None:
        tt_depth, tt_flag, tt_value, tt_best = tt_entry
        tt_move = tt_best
        if tt_depth >= depth:
            if tt_flag == FLAG_EXACT:
                return tt_value
            if tt_flag == FLAG_LOWER:
                if tt_value > alpha:
                    alpha = tt_value
            elif tt_flag == FLAG_UPPER:
                if tt_value < beta:
                    beta = tt_value
            if alpha >= beta:
                return tt_value

    best = -INF
    best_move = None

    for m in _ordered_moves(you, opp, tt_move):
        ny, no, extra = _apply_move(you, opp, m)
        if extra:
            val = _search(ny, no, depth, alpha, beta)
        else:
            val = -_search(no, ny, depth - 1, -beta, -alpha)

        if val > best:
            best = val
            best_move = m
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best <= alpha_orig:
        flag = FLAG_UPPER
    elif best >= beta_orig:
        flag = FLAG_LOWER
    else:
        flag = FLAG_EXACT

    old = _TT.get(key)
    if old is None or depth >= old[0] or flag == FLAG_EXACT:
        _TT[key] = (depth, flag, best, best_move)

    return best


def _search_root(you, opp, depth):
    key = (you, opp)
    tt_entry = _TT.get(key)
    tt_move = tt_entry[3] if tt_entry is not None else None

    alpha = -INF
    beta = INF
    best = -INF
    best_move = None

    for m in _ordered_moves(you, opp, tt_move):
        ny, no, extra = _apply_move(you, opp, m)
        if extra:
            val = _search(ny, no, depth, alpha, beta)
        else:
            val = -_search(no, ny, depth - 1, -beta, -alpha)

        if val > best:
            best = val
            best_move = m
        if val > alpha:
            alpha = val

    if best_move is not None:
        old = _TT.get(key)
        if old is None or depth >= old[0]:
            _TT[key] = (depth, FLAG_EXACT, best, best_move)

    return best, best_move


def _fast_best_move(you, opp):
    key = (you, opp)
    tt_entry = _TT.get(key)
    tt_move = tt_entry[3] if tt_entry is not None else None

    moves = _ordered_moves(you, opp, tt_move)
    best_move = moves[0]
    best_val = -INF

    for m in moves:
        ny, no, extra = _apply_move(you, opp, m)
        if extra:
            val = _evaluate(ny, no)
        else:
            val = -_evaluate(no, ny)

        if val > best_val:
            best_val = val
            best_move = m

    return best_move


def policy(you: list[int], opponent: list[int]) -> int:
    you = tuple(int(x) for x in you)
    opponent = tuple(int(x) for x in opponent)

    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]

    global _DEADLINE, _NODES

    if len(_TT) > TT_MAX:
        _TT.clear()
    if len(_EXACT_TT) > EXACT_TT_MAX:
        _EXACT_TT.clear()

    best_move = _fast_best_move(you, opponent)

    total = _house_sum(you) + _house_sum(opponent)

    _DEADLINE = perf_counter() + 0.92
    _NODES = 0

    if total <= EXACT_TOTAL:
        try:
            best_val = -INF
            tt_entry = _TT.get((you, opponent))
            tt_move = tt_entry[3] if tt_entry is not None else None
            for m in _ordered_moves(you, opponent, tt_move):
                ny, no, extra = _apply_move(you, opponent, m)
                if extra:
                    val = _exact(ny, no)
                else:
                    val = -_exact(no, ny)
                if val > best_val:
                    best_val = val
                    best_move = m
        except _Timeout:
            pass
        return best_move if you[best_move] > 0 else legal[0]

    try:
        depth = 1
        max_depth = 30
        while depth <= max_depth:
            _, move = _search_root(you, opponent, depth)
            if move is not None:
                best_move = move
            depth += 1
    except _Timeout:
        pass

    return best_move if you[best_move] > 0 else legal[0]
