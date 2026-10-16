
from functools import lru_cache
from time import perf_counter
import sys

sys.setrecursionlimit(10000)

_INF = 10**9
_TIME_BUDGET = 0.94
_TIME_CHECK_MASK = 127  # check clock every 128 nodes
_MAX_TT = 200000
_ROOT_EXACT_THRESHOLD = 12
_NODE_EXACT_THRESHOLD = 10
_QDEPTH = 2

_TT = {}
_DEADLINE = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


def _house_sum(side):
    return side[0] + side[1] + side[2] + side[3] + side[4] + side[5]


def _mobility(side):
    return (
        (side[0] > 0)
        + (side[1] > 0)
        + (side[2] > 0)
        + (side[3] > 0)
        + (side[4] > 0)
        + (side[5] > 0)
    )


def _extra_turn_count(side):
    c = 0
    for i in range(6):
        s = side[i]
        if s > 0 and (i + s) % 13 == 6:
            c += 1
    return c


def _terminal_value(you, opp, hy=None, ho=None):
    if hy is None:
        hy = _house_sum(you)
        ho = _house_sum(opp)
    return (you[6] + hy) - (opp[6] + ho)


def _evaluate(you, opp):
    hy = _house_sum(you)
    ho = _house_sum(opp)
    if hy == 0 or ho == 0:
        return _terminal_value(you, opp, hy, ho)

    store_diff = you[6] - opp[6]
    pos_diff = (
        (you[0] - opp[0])
        + 2 * (you[1] - opp[1])
        + 3 * (you[2] - opp[2])
        + 4 * (you[3] - opp[3])
        + 5 * (you[4] - opp[4])
        + 6 * (you[5] - opp[5])
    )
    mobility_diff = _mobility(you) - _mobility(opp)
    extra_diff = _extra_turn_count(you) - _extra_turn_count(opp)

    remaining = hy + ho
    late = 48 - remaining
    if late < 0:
        late = 0
    store_weight = 24 + late // 4

    return (
        store_weight * store_diff
        + pos_diff
        + (hy - ho)
        + 2 * mobility_diff
        + 12 * extra_diff
    )


def _make_move(you, opp, move):
    y = list(you)
    o = list(opp)

    stones = y[move]
    y[move] = 0

    if stones >= 13:
        q, r = divmod(stones, 13)
        y[0] += q
        y[1] += q
        y[2] += q
        y[3] += q
        y[4] += q
        y[5] += q
        y[6] += q
        o[0] += q
        o[1] += q
        o[2] += q
        o[3] += q
        o[4] += q
        o[5] += q
    else:
        r = stones

    step = 1
    while step <= r:
        pos = move + step
        if pos >= 13:
            pos -= 13
        if pos < 6:
            y[pos] += 1
        elif pos == 6:
            y[6] += 1
        else:
            o[pos - 7] += 1
        step += 1

    last = (move + stones) % 13
    same_turn = (last == 6)

    if last < 6 and y[last] == 1:
        opp_idx = 5 - last
        captured = o[opp_idx]
        if captured > 0:
            y[6] += captured + 1
            y[last] = 0
            o[opp_idx] = 0

    hy = y[0] + y[1] + y[2] + y[3] + y[4] + y[5]
    ho = o[0] + o[1] + o[2] + o[3] + o[4] + o[5]

    if hy == 0:
        o[6] += ho
        o[0] = o[1] = o[2] = o[3] = o[4] = o[5] = 0
    elif ho == 0:
        y[6] += hy
        y[0] = y[1] = y[2] = y[3] = y[4] = y[5] = 0

    return tuple(y), tuple(o), same_turn


def _ordered_moves(you, opp, preferred=-1, tactical_only=False):
    base_diff = you[6] - opp[6]
    moves = []

    for m in range(6):
        if you[m] <= 0:
            continue

        ny, no, same_turn = _make_move(you, opp, m)
        delta = (ny[6] - no[6]) - base_diff

        ny_empty = not (ny[0] or ny[1] or ny[2] or ny[3] or ny[4] or ny[5])
        no_empty = not (no[0] or no[1] or no[2] or no[3] or no[4] or no[5])
        tactical = same_turn or delta >= 2 or ny_empty or no_empty

        if tactical_only and not tactical:
            continue

        pri = (
            (500000 if m == preferred else 0)
            + (10000 if same_turn else 0)
            + 64 * delta
            + m
        )
        moves.append((pri, m, ny, no, same_turn))

    moves.sort(key=lambda t: t[0], reverse=True)
    return moves


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & _TIME_CHECK_MASK) == 0 and perf_counter() >= _DEADLINE:
        raise _Timeout


def _quiescence(you, opp, alpha, beta, qdepth):
    _check_time()

    hy = _house_sum(you)
    ho = _house_sum(opp)
    if hy == 0 or ho == 0:
        return _terminal_value(you, opp, hy, ho)

    stand_pat = _evaluate(you, opp)
    if qdepth <= 0:
        return stand_pat

    if stand_pat >= beta:
        return stand_pat
    if stand_pat > alpha:
        alpha = stand_pat

    for _, m, ny, no, same_turn in _ordered_moves(you, opp, tactical_only=True):
        if same_turn:
            val = _quiescence(ny, no, alpha, beta, qdepth - 1)
        else:
            val = -_quiescence(no, ny, -beta, -alpha, qdepth - 1)

        if val >= beta:
            return val
        if val > alpha:
            alpha = val

    return alpha


@lru_cache(maxsize=200000)
def _exact_value(you, opp):
    hy = _house_sum(you)
    ho = _house_sum(opp)
    if hy == 0 or ho == 0:
        return _terminal_value(you, opp, hy, ho)

    best = -_INF
    for m in range(6):
        if you[m] <= 0:
            continue
        ny, no, same_turn = _make_move(you, opp, m)
        if same_turn:
            val = _exact_value(ny, no)
        else:
            val = -_exact_value(no, ny)
        if val > best:
            best = val
    return best


def _search(you, opp, depth, alpha, beta):
    _check_time()

    hy = _house_sum(you)
    ho = _house_sum(opp)
    if hy == 0 or ho == 0:
        return _terminal_value(you, opp, hy, ho)

    if hy + ho <= _NODE_EXACT_THRESHOLD:
        return _exact_value(you, opp)

    if depth <= 0:
        return _quiescence(you, opp, alpha, beta, _QDEPTH)

    key = (you, opp)
    orig_alpha = alpha
    orig_beta = beta
    preferred = -1

    entry = _TT.get(key)
    if entry is not None:
        entry_depth, flag, val, best_move = entry
        preferred = best_move
        if entry_depth >= depth:
            if flag == 0:
                return val
            if flag > 0:
                if val > alpha:
                    alpha = val
            else:
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val

    best = -_INF
    best_move = -1

    for _, m, ny, no, same_turn in _ordered_moves(you, opp, preferred=preferred):
        if same_turn:
            val = _search(ny, no, depth, alpha, beta)
        else:
            val = -_search(no, ny, depth - 1, -beta, -alpha)

        if val > best:
            best = val
            best_move = m

        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    if len(_TT) < _MAX_TT:
        flag = 0
        if best <= orig_alpha:
            flag = -1
        elif best >= orig_beta:
            flag = 1
        _TT[key] = (depth, flag, best, best_move)

    return best


def _search_root(you, opp, depth):
    entry = _TT.get((you, opp))
    preferred = entry[3] if entry is not None else -1
    moves = _ordered_moves(you, opp, preferred=preferred)

    best = -_INF
    best_move = moves[0][1]
    alpha = -_INF
    beta = _INF

    for _, m, ny, no, same_turn in moves:
        if same_turn:
            val = _search(ny, no, depth, alpha, beta)
        else:
            val = -_search(no, ny, depth - 1, -beta, -alpha)

        if val > best:
            best = val
            best_move = m

        if val > alpha:
            alpha = val

    if len(_TT) < _MAX_TT:
        _TT[(you, opp)] = (depth, 0, best, best_move)

    return best, best_move


def policy(you, opponent):
    yt = tuple(you)
    ot = tuple(opponent)

    legal = [i for i in range(6) if yt[i] > 0]
    if len(legal) == 1:
        return legal[0]

    # Small opening book for the standard initial position.
    if yt == (4, 4, 4, 4, 4, 4, 0) and ot == (4, 4, 4, 4, 4, 4, 0):
        return 2

    if len(_TT) > _MAX_TT:
        _TT.clear()

    total = _house_sum(yt) + _house_sum(ot)

    entry = _TT.get((yt, ot))
    preferred = entry[3] if entry is not None else -1
    ordered = _ordered_moves(yt, ot, preferred=preferred)

    if ordered:
        best_move = ordered[0][1]
    else:
        for i in range(6):
            if yt[i] > 0:
                return i
        return 0  # unreachable safety

    if total <= _ROOT_EXACT_THRESHOLD:
        best_val = -_INF
        for _, m, ny, no, same_turn in ordered:
            if same_turn:
                val = _exact_value(ny, no)
            else:
                val = -_exact_value(no, ny)
            if val > best_val:
                best_val = val
                best_move = m
        return best_move

    global _DEADLINE, _NODES
    _DEADLINE = perf_counter() + _TIME_BUDGET
    _NODES = 0

    if total > 34:
        max_depth = 10
    elif total > 22:
        max_depth = 12
    else:
        max_depth = 16

    for depth in range(1, max_depth + 1):
        try:
            _, move = _search_root(yt, ot, depth)
            if 0 <= move <= 5 and yt[move] > 0:
                best_move = move
        except _Timeout:
            break

    if yt[best_move] > 0:
        return best_move

    for i in range(6):
        if yt[i] > 0:
            return i

    return 0
