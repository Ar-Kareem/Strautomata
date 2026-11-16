
from __future__ import annotations

import time

WIN_SCALE = 1_000_000
INF = 10**18

_TT = {}
_HISTORY = [0, 0, 0, 0, 0, 0]
_DEADLINE = 0.0
_NODES = 0


class _SearchTimeout(Exception):
    pass


def _hs(s):
    return s[0] + s[1] + s[2] + s[3] + s[4] + s[5]


def _tick():
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout()


def _terminal_value(me, opp):
    ms = _hs(me)
    os = _hs(opp)
    return ((me[6] + ms) - (opp[6] + os)) * WIN_SCALE


def _make_move(me, opp, move):
    """Return new_me, new_opp, extra_turn, terminal after move by me[move]."""
    n = me[move]

    m = list(me)
    o = list(opp)
    m[move] = 0

    # There are 13 sowing locations: 6 own houses, own store, 6 opponent houses.
    q, r = divmod(n, 13)

    if q:
        m[0] += q
        m[1] += q
        m[2] += q
        m[3] += q
        m[4] += q
        m[5] += q
        m[6] += q
        o[0] += q
        o[1] += q
        o[2] += q
        o[3] += q
        o[4] += q
        o[5] += q

    pos = move
    for _ in range(r):
        pos += 1
        if pos == 13:
            pos = 0

        if pos < 6:
            m[pos] += 1
        elif pos == 6:
            m[6] += 1
        else:
            o[pos - 7] += 1

    final = (move + n) % 13
    extra = final == 6

    # Capture.
    if final < 6 and m[final] == 1:
        oi = 5 - final
        captured = o[oi]
        if captured > 0:
            m[6] += captured + 1
            m[final] = 0
            o[oi] = 0

    ms = m[0] + m[1] + m[2] + m[3] + m[4] + m[5]
    os = o[0] + o[1] + o[2] + o[3] + o[4] + o[5]
    terminal = ms == 0 or os == 0

    if terminal:
        m[6] += ms
        o[6] += os
        m[0] = m[1] = m[2] = m[3] = m[4] = m[5] = 0
        o[0] = o[1] = o[2] = o[3] = o[4] = o[5] = 0

    return tuple(m), tuple(o), extra, terminal


def _tactical(side, other):
    """Cheap tactical features for side to move."""
    legal = 0
    extra = 0
    cap_max = 0
    cap_sum = 0
    store_potential = 0

    for i in range(6):
        n = side[i]
        if n <= 0:
            continue

        legal += 1

        q, r = divmod(n, 13)
        store_potential += q
        if r >= 6 - i:
            store_potential += 1

        p = (i + n) % 13
        if p == 6:
            extra += 1
        elif p < 6 and n <= 13 and (p == i or side[p] == 0):
            c = other[5 - p]
            if c > 0:
                cap = c + 1
                cap_sum += cap
                if cap > cap_max:
                    cap_max = cap

    return legal, extra, cap_max, cap_sum, store_potential


def _evaluate(me, opp):
    """Static value from the current side-to-move's perspective."""
    ms = _hs(me)
    os = _hs(opp)

    if ms == 0 or os == 0:
        return ((me[6] + ms) - (opp[6] + os)) * WIN_SCALE

    store_diff = me[6] - opp[6]
    house_diff = ms - os

    # Seeds nearer to the store are slightly more useful.
    my_pos = me[1] + 2 * me[2] + 3 * me[3] + 4 * me[4] + 5 * me[5]
    op_pos = opp[1] + 2 * opp[2] + 3 * opp[3] + 4 * opp[4] + 5 * opp[5]

    score = 120 * store_diff + 6 * house_diff + 3 * (my_pos - op_pos)

    ml, mex, mcap, mcaps, mstorepot = _tactical(me, opp)
    ol, oex, ocap, ocaps, ostorepot = _tactical(opp, me)

    score += 45 * (mex - oex)
    score += 18 * (mcap - ocap) + 5 * (mcaps - ocaps)
    score += 8 * (mstorepot - ostorepot)
    score += 4 * (ml - ol)

    # Empty own houses opposite loaded opponent houses are capture targets.
    trap = 0
    for i in range(6):
        if me[i] == 0:
            trap += opp[5 - i]
        if opp[i] == 0:
            trap -= me[5 - i]
    score += 2 * trap

    # In late games, seeds already controlled on our side become closer to final score.
    total_houses = ms + os
    if total_houses < 24:
        end_balance = (me[6] + ms) - (opp[6] + os)
        score += (24 - total_houses) * 3 * end_balance

    return score


def _ordered_children(me, opp, tt_best):
    children = []
    ms_before = _hs(me)
    os_before = _hs(opp)

    for i in range(6):
        if me[i] <= 0:
            continue

        nm, no, extra, terminal = _make_move(me, opp, i)

        nm_h = _hs(nm)
        no_h = _hs(no)
        store_gain = nm[6] - me[6]

        score = 0
        if i == tt_best:
            score += 10_000_000

        if terminal:
            score += (nm[6] - no[6]) * 1_000_000

        if extra:
            score += 80_000

        # Prefer direct scoring, captures, and moves that do not feed the opponent.
        score += store_gain * 1000
        score += (os_before - no_h) * 250
        score += (nm_h - ms_before) * 15
        score += i * 4
        score += _HISTORY[i] >> 2

        # If the turn is passed, avoid handing the opponent an obvious tactic.
        if not terminal and not extra:
            _, oe, ocap, _, osp = _tactical(no, nm)
            score -= oe * 4000 + ocap * 700 + osp * 20

        children.append((score, i, nm, no, extra, terminal))

    children.sort(key=lambda x: x[0], reverse=True)
    return children


def _child_value(nm, no, extra, terminal, depth, alpha, beta):
    if terminal:
        return _terminal_value(nm, no)
    if extra:
        return _search(nm, no, depth, alpha, beta)
    return -_search(no, nm, depth - 1, -beta, -alpha)


def _search(me, opp, depth, alpha, beta):
    _tick()

    ms = _hs(me)
    os = _hs(opp)

    if ms == 0 or os == 0:
        return ((me[6] + ms) - (opp[6] + os)) * WIN_SCALE

    if depth <= 0:
        return _evaluate(me, opp)

    key = (me, opp)
    entry = _TT.get(key)
    tt_best = -1

    if entry is not None:
        edepth, flag, value, best_move = entry
        tt_best = best_move
        if edepth >= depth:
            if flag == 0:
                return value
            if flag > 0 and value >= beta:
                return value
            if flag < 0 and value <= alpha:
                return value

    alpha_orig = alpha
    beta_orig = beta

    children = _ordered_children(me, opp, tt_best)
    if not children:
        return ((me[6] + ms) - (opp[6] + os)) * WIN_SCALE

    best_val = -INF
    best_move = children[0][1]
    first = True

    for _, move, nm, no, extra, terminal in children:
        if first:
            val = _child_value(nm, no, extra, terminal, depth, alpha, beta)
            first = False
        else:
            # Principal variation search / null-window probe.
            val = _child_value(nm, no, extra, terminal, depth, alpha, alpha + 1)
            if alpha < val < beta:
                val = _child_value(nm, no, extra, terminal, depth, alpha, beta)

        if val > best_val:
            best_val = val
            best_move = move

        if val > alpha:
            alpha = val

        if alpha >= beta:
            _HISTORY[move] += depth * depth + 1
            break

    if best_val <= alpha_orig:
        flag = -1
    elif best_val >= beta_orig:
        flag = 1
    else:
        flag = 0

    _TT[key] = (depth, flag, best_val, best_move)
    return best_val


def _root_search(me, opp, depth, preferred):
    _tick()

    children = _ordered_children(me, opp, preferred)
    if not children:
        return _terminal_value(me, opp), preferred

    alpha = -INF
    beta = INF
    best_val = -INF
    best_move = children[0][1]
    first = True

    for _, move, nm, no, extra, terminal in children:
        if first:
            val = _child_value(nm, no, extra, terminal, depth, alpha, beta)
            first = False
        else:
            val = _child_value(nm, no, extra, terminal, depth, alpha, alpha + 1)
            if alpha < val < beta:
                val = _child_value(nm, no, extra, terminal, depth, alpha, beta)

        if val > best_val:
            best_val = val
            best_move = move

        if val > alpha:
            alpha = val

    _TT[(me, opp)] = (depth, 0, best_val, best_move)
    return best_val, best_move


def _greedy_move(me, opp, legal=None):
    if legal is None:
        legal = [i for i in range(6) if me[i] > 0]

    if not legal:
        return 0

    best = legal[0]
    best_val = -INF

    for i in legal:
        nm, no, extra, terminal = _make_move(me, opp, i)

        if terminal:
            val = _terminal_value(nm, no)
        elif extra:
            val = _evaluate(nm, no)
        else:
            val = -_evaluate(no, nm)

        val += (nm[6] - me[6]) * 10
        if extra:
            val += 100

        if val > best_val:
            best_val = val
            best = i

    return best


def policy(you: list[int], opponent: list[int]) -> int:
    global _DEADLINE, _NODES

    try:
        me = tuple(int(x) for x in you)
        opp = tuple(int(x) for x in opponent)

        legal = [i for i in range(6) if me[i] > 0]
        if not legal:
            return 0
        if len(legal) == 1:
            return int(legal[0])

        # Standard 6x4 opening: pit 2 gives an immediate extra turn.
        if me == (4, 4, 4, 4, 4, 4, 0) and opp == (4, 4, 4, 4, 4, 4, 0):
            return 2

        fallback = _greedy_move(me, opp, legal)
        best = fallback
        best_val = -INF

        if len(_TT) > 250_000:
            _TT.clear()

        if max(_HISTORY) > 1_000_000:
            for i in range(6):
                _HISTORY[i] //= 2

        total_houses = _hs(me) + _hs(opp)

        # Leave a safety margin under the 1-second limit.
        budget = 0.88 if total_houses <= 18 else 0.84
        _DEADLINE = time.perf_counter() + budget
        _NODES = 0

        if total_houses <= 10:
            max_depth = 100
        elif total_houses <= 18:
            max_depth = 70
        elif total_houses <= 28:
            max_depth = 45
        else:
            max_depth = 30

        for depth in range(1, max_depth + 1):
            if time.perf_counter() >= _DEADLINE:
                break

            try:
                val, mv = _root_search(me, opp, depth, best)
            except _SearchTimeout:
                break

            if 0 <= mv < 6 and me[mv] > 0:
                best = mv
                best_val = val

            # A non-draw terminal result has been proven within the searched line.
            if abs(best_val) >= WIN_SCALE and best_val % WIN_SCALE == 0:
                break

            if _DEADLINE - time.perf_counter() < 0.008:
                break

        if not (0 <= best < 6 and me[best] > 0):
            best = fallback
        if not (0 <= best < 6 and me[best] > 0):
            best = legal[0]

        return int(best)

    except Exception:
        # Absolute safety fallback: return the first legal move from the raw input.
        for i in range(6):
            try:
                if you[i] > 0:
                    return int(i)
            except Exception:
                pass
        return 0
